from clutch.observe import live_call


def test_gemini_launcher_labels():
    root = (10, 1, "clutch drain")
    for path, model in [
        ("/home/u/.nvm/versions/node/v24.15.0/bin/gemini", "gemini-3.1-flash-lite"),
        ("/p/global/5/.pnpm/@google+gemini-cli@0.49.0/node_modules/@google/gemini-cli/bundle/gemini.js", "gemini-3.1-pro-preview"),
    ]:
        args = f"{path} --skip-trust -m {model} -o stream-json"
        assert live_call([root, (11, 10, f"node {args}"), (12, 11, f"/home/u/.nvm/versions/node/v24.15.0/bin/node --max-old-space-size=20054 {args}")], 10) == f"gemini {model}"
    assert live_call([root, (11, 10, "node /bin/gemini")], 10) == "gemini ?"
    assert live_call([root, (11, 10, "node /usr/lib/node_modules/npm/bin/npm-cli.js install")], 10) == ""
