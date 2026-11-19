"""Deterministic image checks and in-memory operator previews."""

from io import BytesIO
from pathlib import Path

MIN_DIMENSION = 32
MAX_DIMENSION = 16384
MAX_ASPECT_RATIO = 10
MIN_VARIANCE = 20.0
COPY_DISTANCE = 1
BASE_COPY_DISTANCE = 1
MIN_SSIM = 0.65
MIN_ORB_MATCHES = 4
MIN_EMBED_SIMILARITY = 0.25
PREVIEW_SIZE = 256


def _load():
    import cv2
    import imagehash
    import numpy as np
    from PIL import Image
    from skimage.metrics import structural_similarity

    return Image, np, imagehash, cv2, structural_similarity


def _embedder():
    import open_clip
    import torch

    model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    model.eval()

    def embed(images):
        with torch.no_grad():
            vectors = model.encode_image(torch.stack([preprocess(image) for image in images]))
            return vectors / vectors.norm(dim=-1, keepdim=True)

    return embed


def _preservation(source, candidate, np, ssim):
    size = (PREVIEW_SIZE, PREVIEW_SIZE)
    left = np.asarray(source.resize(size).convert("L"))
    right = np.asarray(candidate.resize(size).convert("L"))
    return ssim(left, right, data_range=255)


def _presence(source, candidate, np, cv2):
    orb = cv2.ORB_create(nfeatures=1000, edgeThreshold=5, fastThreshold=10)
    _, source_descriptors = orb.detectAndCompute(np.asarray(source.convert("L")), None)
    _, candidate_descriptors = orb.detectAndCompute(np.asarray(candidate.convert("L")), None)
    if source_descriptors is None or candidate_descriptors is None:
        return 0
    pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(source_descriptors, candidate_descriptors, k=2)
    return sum(1 for pair in pairs if len(pair) == 2 and pair[0].distance < 0.75 * pair[1].distance)


def scores(artifact: Path, inputs: list[Path]) -> tuple[float | None, int | None]:
    Image, np, _, cv2, ssim = _load()
    with Image.open(artifact) as image:
        candidate = image.convert("RGB")
    preservation, presence = None, None
    for index, path in enumerate(inputs):
        with Image.open(path) as image:
            source = image.convert("RGB")
        if index == 0:
            preservation = _preservation(source, candidate, np, ssim)
        else:
            presence = (presence or 0) + _presence(source, candidate, np, cv2)
    return preservation, presence


def judge(artifact: Path, inputs: list[Path], *, embedding: bool = False) -> list[str]:
    """Return one diagnostic for each failed applicable check."""
    try:
        Image, np, imagehash, cv2, ssim = _load()
    except ImportError:
        return [f"{artifact}: image checks require clutchwork[images]; install clutchwork[images]"]
    if not artifact.is_file():
        return [f"{artifact}: exists check failed"]
    try:
        with Image.open(artifact) as image:
            candidate = image.convert("RGB")
    except OSError, ValueError:
        return [f"{artifact}: decode check failed"]
    if embedding and len(inputs) > 1:
        try:
            embed = _embedder()
        except ImportError:
            return [f"{artifact}: embedding checks require clutchwork[images-embed]; install clutchwork[images-embed]"]
    failures = []
    width, height = candidate.size
    if min(width, height) < MIN_DIMENSION or max(width, height) > MAX_DIMENSION or max(width, height) / min(width, height) > MAX_ASPECT_RATIO:
        failures.append(f"{artifact}: dimensions/aspect ratio check failed")
    if np.asarray(candidate, dtype=np.float64).var(axis=(0, 1)).mean() < MIN_VARIANCE:
        failures.append(f"{artifact}: not-blank check failed")
    candidate_hash = imagehash.phash(candidate)
    for index, path in enumerate(inputs):
        try:
            with Image.open(path) as image:
                source = image.convert("RGB")
            identical = artifact.read_bytes() == path.read_bytes()
        except OSError, ValueError:
            failures.append(f"{path}: input decode check failed")
            continue
        floor = BASE_COPY_DISTANCE if index == 0 else COPY_DISTANCE
        if identical or candidate_hash - imagehash.phash(source) <= floor:
            failures.append(f"{artifact}: not-a-copy check failed for {path}")
        if index == 0:
            if _preservation(source, candidate, np, ssim) < MIN_SSIM:
                failures.append(f"{artifact}: preservation check failed against {path}")
        else:
            if embedding:
                views = [candidate.crop((x * width // 3, y * height // 3, (x + 1) * width // 3, (y + 1) * height // 3)) for y in range(3) for x in range(3)] + [candidate]
                vectors = embed([source, *views])
                if max(float((vectors[0] * vector).sum()) for vector in vectors[1:]) < MIN_EMBED_SIMILARITY:
                    failures.append(f"{path}: presence check failed in {artifact} (embedding)")
            elif _presence(source, candidate, np, cv2) < MIN_ORB_MATCHES:
                failures.append(f"{path}: presence check failed in {artifact}")
    return failures


def side_by_side(paths: list[Path]) -> bytes:
    Image, _, _, _, _ = _load()
    images = []
    for path in paths:
        with Image.open(path) as image:
            images.append(image.convert("RGB"))
    canvas = Image.new("RGB", (sum(image.width for image in images), max(image.height for image in images)))
    x = 0
    for image in images:
        canvas.paste(image, (x, 0))
        x += image.width
    output = BytesIO()
    canvas.save(output, format="PNG")
    return output.getvalue()


def heatmap(base: Path, artifact: Path) -> bytes:
    Image, np, _, _, _ = _load()
    with Image.open(base) as image:
        original = image.convert("RGB")
    with Image.open(artifact) as image:
        candidate = image.convert("RGB").resize(original.size)
    difference = np.abs(np.asarray(original, dtype=np.int16) - np.asarray(candidate, dtype=np.int16)).max(axis=2).astype(np.uint8)
    heat = np.zeros((*difference.shape, 3), dtype=np.uint8)
    heat[:, :, 0] = difference
    output = BytesIO()
    Image.fromarray(heat).save(output, format="PNG")
    return output.getvalue()
