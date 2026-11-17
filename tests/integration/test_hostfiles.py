"""Core renderer contract; regenerate the golden with uv run python -m tests.test_hostfiles."""

import asyncio
import base64
import builtins
import re
from pathlib import Path

import pytest

from clutch import hostfiles
from clutch.seams import LocalFileSystem
from tests.integration.test_cli import root
from tests.integration.test_git import commit_lock
from tests.integration.test_merge import repo
from tests.integration.test_stages import agent, verdict

REPO = Path(__file__).resolve().parents[2]
GOLDEN = b"PCEtLSBjbHV0Y2g6Y29yZSBiZWdpbiAtLT4KIyMgVGlja2V0IGF1dGhvcmluZyAtLSByZWFkIGJlZm9yZSB3cml0aW5nIGFueSB0aWNrZXQKClRoZXNlIHJ1bGVzIGNvbWUgZmlyc3QgYmVjYXVzZSBzZXNzaW9ucyB0aGF0IHNraW0gbWlzcyB0aGVtLiBIQVJEIHJ1bGVzIGhhdmUgbm8gZXhjZXB0aW9ucy4gVGhleSBhcmUgYmVoYXZpb3JhbDogbm8gZ2F0ZSBjYW4ganVkZ2UgdGhlbSwgc28gbmV2ZXIgZmlsZSBhbiBlbmZvcmNlbWVudCB0aWNrZXQgZm9yIG9uZS4KCi0gSEFSRDogSW4gYW4gaW50ZXJhY3RpdmUgY2hhdCwgZXZlcnkgcmVxdWVzdGVkIGNoYW5nZSB0byByZXBvIGNvbnRlbnQgKGNvZGUsIGRvY3MsIENMQVVERS5tZCwgQUdFTlRTLm1kLCBzZXR0aW5ncywgaG9va3MsIHNjcmlwdHMsIGNvbmZpZywgYWdlbnQgcnVsZXMpIGJlY29tZXMgYSBkcmFmdGVkIHRpY2tldCBhdCBgdGlja2V0cy88c3RlbT4vdGlja2V0Lm1kYCwgdGhlbiBzdG9wLiBOZXZlciBlZGl0IG9yIGNvbW1pdCBvbiBtYWluLiBUaGUgb25seSBleGNlcHRpb25zOiAoMSkgdGhlIHVzZXIgc2F5cyAiZWRpdCBtYWluIiwgImNvbW1pdCBkaXJlY3RseSIsICJza2lwIHRoZSB0aWNrZXQiLCAiZG8gaXQgaW5saW5lIiwgb3IgYW4gZXF1YWxseSBleHBsaWNpdCBvdmVycmlkZSB0aGlzIHR1cm47IGFuZ2VyIHdvcmRzIGFsb25lIGRvIG5vdCBjb3VudDsgKDIpIHlvdSBhcmUgaW4gYSBjbHV0Y2ggdGlja2V0IHdvcmt0cmVlOyAoMykgdGhlIHVzZXIgbmFtZXMgYnkgcGF0aCBhIGZpbGUgdW5kZXIgYW4gZXhpc3RpbmcgYHRpY2tldHMvPHN0ZW0+L2AgdG8gZWRpdCBvciBkZWxldGU7ICg0KSByZWFkLW9ubHkgaW5zcGVjdGlvbjsgKDUpIHRoZSBzdXBlcnZpc2luZyBmaXhlcyBiZWxvdy4gSWYgeW91IGFscmVhZHkgZWRpdGVkIG1haW4gd2l0aG91dCBhbiBvdmVycmlkZSwgc3RvcCwgc2F5IHNvLCBhbmQgYXNrIHdoZXRoZXIgdG8gcmV2ZXJ0IGFuZCByZWZpbGUuIFdoeTogY2hhdCBlZGl0cyBza2lwIHRoZSB0aWNrZXQsIHJ1biByZWNvcmQsIHJldmlldywgYW5kIHJldHJvIHRoYXQgbWFrZSBjbHV0Y2ggZGVidWdnYWJsZS4KLSBIQVJEOiBOZXZlciB3cml0ZSBhIHRpY2tldCBmcm9tIG1lbW9yeS4gUnVuIGBjbHV0Y2ggdGlja2V0IG5ldyA8c3RlbT4gLS1raW5kIGZlYXR1cmV8YnVnfGNob3JlYDsgaXQgd3JpdGVzIHRoZSBza2VsZXRvbiBhbmQgcHJpbnRzIHRoZSBwYXRoIG9mIHRoZSB0aWNrZXQgYXV0aG9yaW5nIGd1aWRlIGluIHlvdXIgY2x1dGNoIGluc3RhbGwgKGZvciBhbiBleGlzdGluZyB0aWNrZXQsIGl0cyByZWZ1c2FsIHByaW50cyB0aGUgc2FtZSBwYXRoKS4gUmVhZCB0aGF0IGxvY2FsIGZpbGUgaW4gZnVsbC4gYGNsdXRjaCBob3N0IGRvY3NgIHByaW50cyB0aGUgaW5zdGFsbGVkIHBhdGhzIG9mIGFsbCBob3N0IGd1aWRlczsgcmVhZCB0aGVtIGxvY2FsbHksIG5ldmVyIGZyb20gYSBVUkwuIEZpbGwgZXZlcnkgc2VjdGlvbiwgcnVuIGBjbHV0Y2ggdGlja2V0IGxpbnQgPHN0ZW0+YCB1bnRpbCBpdCBleGl0cyAwLCB0aGVuIHJ1biBgY2x1dGNoIHRpY2tldCByZXZpZXcgPHN0ZW0+YCBhbmQgcmVwYWlyIGV2ZXJ5IGZpbmRpbmcgdW50aWwgaXQgcHJpbnRzIGFwcHJvdmUuIFRpY2tldHMgYXJlIG1hcmtkb3duIGZpbGVzLCBuZXZlciBpc3N1ZS10cmFja2VyIGl0ZW1zLiBXaHk6IHN0YWxlIHRpY2tldCBzaGFwZXMgYnJlYWsgcnVucyBiZWZvcmUgaW1wbGVtZW50YXRpb24gc3RhcnRzLgotIEZlbmNlIGV2ZXJ5IGZpbGUgdGhlIGNoYW5nZSBmb3JjZXMsIGluY2x1ZGluZyBjYWxsZXJzLCBpbXBvcnRlcnMsIGRvY3VtZW50cyBpdCBjaGFuZ2VzLCBhbmQgdGVzdHMgdGhhdCBwaW4gYSBjaGFuZ2VkIG5hbWUsIHZhbHVlLCBvciB2ZXJzaW9uLiBXaHk6IGEgZm9yY2VkIGZpbGUgb3V0c2lkZSB0aGUgZmVuY2UgbWFrZXMgdGhlIHRpY2tldCBpbXBvc3NpYmxlLgotIEZyb250bWF0dGVyIGhvbGRzIG9ubHkgZmllbGRzIHJlYWQgYnkgc2NoZWR1bGluZywgZ2F0ZXMsIG9yIGF1dGhvcmluZy90cmlhZ2UgcG9saWN5OyBgIyMgRGVwZW5kcyBvbmAgbmFtZXMgb25seSBuZWVkZWQgbWVyZ2VkIGNvZGU7IHB1dCBhbGwgb3RoZXIgb3JkZXJpbmcgaW4gcHJpb3JpdHkgb3IgYCMjIFJ1bnMgYmVmb3JlYCwgbmV2ZXIgaW4gcHJvc2UuCi0gSEFSRDogV2hlbiBhIHJlcG9ydGVkIHByb2JsZW0gaGFzIGEgY2F1c2UgdGhhdCB3aWxsIHJlY3VyLCB3cml0ZSB0d28gc2VwYXJhdGUgdGlja2V0cyBpbiB0aGUgc2FtZSB0dXJuLiBGaXJzdCB0aGUgaW5zdGFuY2UgZml4OiBtaW5pbWFsIHNjb3BlLCB3cml0dGVuIGJlZm9yZSBhbnkgY2F1c2UgZGlhZ25vc2lzLiBUaGVuIHRoZSBjYXVzZSBmaXgsIG5ldmVyIGZvbGRlZCBpbnRvIHRoZSBpbnN0YW5jZTsgdGhlIHR1cm4gaXMgdW5maW5pc2hlZCB1bnRpbCBpdCBleGlzdHMuIEJvdGggYXJlIHNvbGljaXRlZCwgc28gbm8gYXNrIGlzIG5lZWRlZC4gUm91dGluZzoKICAtIFByb2R1Y3QgaW5zdGFuY2U6IGBwcmlvcml0eTogUDBgLCBubyBibG9ja2luZyBkZXBlbmRzLgogIC0gUHJvZHVjdCBjYXVzZSAoaW5lcnQ7IGRvZXMgbm90IHNwcmVhZCBvbiBpdHMgb3duKTogYHByaW9yaXR5OiBQMWAuIFdoZW4gdGhlIHR3byBzaGFyZSBhbiBlZGl0IHN1cmZhY2UsIHRoZSBpbnN0YW5jZSBsaXN0cyB0aGUgY2F1c2UgaW4gYCMjIFJ1bnMgYmVmb3JlYC4KICAtIE9yY2hlc3RyYXRpb24gY2F1c2UgKHNjaGVkdWxlciwgZ2F0ZSwgZW52aXJvbm1lbnQsIHNoYXJlZCBtb2R1bGUsIGZpeHR1cmUgZm9ybWF0OyBrZWVwcyBicmVha2luZyBydW5zIHdoaWxlIGl0IHNpdHMpOiBgcHJpb3JpdHk6IFAwYCwgYCMjIFJ1bnMgYmVmb3JlYCBldmVyeSB0aWNrZXQgaXQgdW5ibG9ja3MsIG5ldmVyIGRlcGVuZHMgb24gYSBwcm9kdWN0IGluc3RhbmNlLgotIEhBUkQ6IEZvciB0aWNrZXQtd29ydGh5IHdvcmsgdGhlIHVzZXIgZGlkIG5vdCBhc2sgZm9yIChmb2xsb3ctdXAsIHByZXZlbnRpb24sIGVuZm9yY2VtZW50IGxpbnQsIHN3ZWVwKSwgc3RvcCBiZWZvcmUgZGl2aW5nOiBuYW1lIGl0IGluIDEtMiBzZW50ZW5jZXMgYW5kIGFzayB0aGUgdXNlciB0byBjaG9vc2UgYXV0aG9yIG5vdywgYWZ0ZXIgdGhlIGN1cnJlbnQgdGFzaywgb3Igc2tpcC4gIkFmdGVyIiBtYWtlcyBpdCBhbiBvcGVuIHRocmVhZC4gQW5ub3VuY2UgaW4gb25lIGxpbmUgYW55IHVuc29saWNpdGVkIGludmVzdGlnYXRpb24gbG9uZ2VyIHRoYW4gYSBjb3VwbGUgb2YgbWludXRlcy4gVGhlIHVzZXIncyByZXF1ZXN0ZWQgdGFzayBhbHdheXMgZ29lcyBmaXJzdC4gQXV0b25vbW91cyBydW5zIHNraXAgdGhlIGFzayBhbmQgZmlsZSB0byB0aGUgU3VnZ2VzdGlvbiBCb3guCi0gRmlsZSBhbiB1bnJlcXVlc3RlZCBpZGVhIG9yIHNlY29uZCBwcm9ibGVtIHdpdGggYGNsdXRjaCBib3ggc3VnZ2VzdCAiPHN1bW1hcnk+ImAgYW5kIG5hbWUgaXQgaW4gb25lIGxpbmUuIFdoeTogYSBtYXJnaW4gc3VnZ2VzdGlvbiBkaWVzIHdpdGggdGhlIGNoYXQuCi0gQSBzdXBlcnZpc2luZyBzZXNzaW9uIG1heSwgdW5hc2tlZCwgZml4IGEgdGlja2V0J3MgbGludCBvciBmb3JtYXQgZXJyb3JzLCBhZGQgYSBmaWxlIG1pc3NpbmcgZnJvbSBgIyMgU2NvcGUgZmVuY2VgIG9yIGAjIyBDb250ZXh0YCwgY29ycmVjdCBhIHN0YWxlIHBhdGgsIG1ha2UgYSBzaW1wbGUgd29yZGluZyB1cGRhdGUsIGFuZCBydW4gb3IgcmVzdGFydCB0aGUgZHJhaW4uIEl0IG1heSBjb25maXJtIG9yIHJlamVjdCBhbmQgZWRpdCBhbnkgdGlja2V0IG9ubHkgYXMgYSBgY2x1dGNoIHByb21wdCBkaWFnbm9zZWAgb3IgYGNsdXRjaCBwcm9tcHQgZHJhZnRzYCBSZWNvbW1lbmRhdGlvbiBuYW1lcy4gSXQgbWF5IG5vdCByZXRyeSBhIHN0ZW0gd2hvc2UgY2FwcyBhcmUgc3BlbnQgb3IgZWRpdCBhIHJ1bm5pbmcgdGlja2V0OyBjaGFuZ2luZyBhIHRpY2tldCdzIGdvYWwgb3Igc2NvcGUgcmVxdWlyZXMgc3VjaCBhIFJlY29tbWVuZGF0aW9uLgoKIyMgRGlhZ25vc2lzCgotIEhBUkQ6IFdoZW4gYSBydW4gZmFpbHMsIGlzIGtpbGxlZCwgdGltZXMgb3V0LCBzdGFsbHMsIG9yIGVzY2FsYXRlcywgbmFtZSBpdHMgcm9vdCBjYXVzZSBpbiBvbmUgc2VudGVuY2UgYmVmb3JlIGVkaXRpbmcgc3BlYyBvciBjb2RlIG9yIHJlcnVubmluZy4gUmVhZCBgY2x1dGNoIHZpZXcgc3RhdHVzYCwgYHRpY2tldHMvPHN0ZW0+L2AgKGBydW4ubWRgLCBgY2hlY2tzLmpzb25gLCBgZGlhZ25vc2lzLmpzb25gLCBgcmV2aWV3Lm1kYCwgYGF0dGVtcHRzL2ApLCBhbmQgdGhlIGVuZ2luZSBsb2cuIEZpeCB0aGUgY2F1c2Ugd2hlcmUgaXQgbGl2ZXMuIEFuIGV4dGVybmFsIGNhdXNlIChlbmdpbmUsIGdhdGUsIGVudmlyb25tZW50LCBzaGFyZWQgbW9kdWxlLCBmaXh0dXJlLCBmbGFreSB0ZXN0LCB3cm9uZyBwcmVtaXNlKSBpcyBmaXhlZCBmaXJzdCBhbmQgb3JkZXJlZCBhaGVhZCB3aXRoIHByaW9yaXR5IGFuZCBgIyMgUnVucyBiZWZvcmVgLiBEbyBub3QgYXNzdW1lIHRoZSB0aWNrZXQgaXMgd3JvbmcuIE5ldmVyIHJlcnVuIGEgZmxha3kgZmFpbHVyZSB1bnRpbCBpdCBwYXNzZXMgYW5kIGNhbGwgdGhhdCBmaXhlZC4KLSBIQVJEOiBXaGVuIGEgc3ltcHRvbSByZWN1cnMgb24gYSBzdXJmYWNlIGFscmVhZHkgZml4ZWQsIG5hbWUgdGhlIHJvb3QgbW9kZWwgYWdhaW5zdCB0aGUgY2Fub25pY2FsIHNwZWMgKGRlc2lnbiBkb2NzLCBjb250cmFjdHMpIGFuZCB3cml0ZSBhIHJvb3QtY2F1c2UgdGlja2V0LCBub3QgYW5vdGhlciBwYXRjaC4gQSBzY29wZSBmZW5jZSB0aGF0IGZvcmJpZHMgdG91Y2hpbmcgdGhlIHN1c3BlY3RlZCByb290IGlzIGEgcmVkIGZsYWc6IHJlLXNjb3BlIGl0LiBUZXN0cyB0aGF0IGFzc2VydCB0aGUgY3VycmVudCB3cm9uZyBiZWhhdmlvciBwcm92ZSBub3RoaW5nLiBOZXZlciB3cml0ZSAidGhlIGRlZmVjdCB3YXMgbm90IFgiIHdpdGhvdXQgY2hlY2tpbmcgdGhlIHNwZWMuCi0gSEFSRDogV2l0aCBldmVyeSBmaXggb3IgZGlhZ25vc2lzLCBuYW1lIHRoZSBjaGFuZ2UgdGhhdCBzdG9wcyB0aGUgd2hvbGUgY2xhc3MgZnJvbSByZWN1cnJpbmcgKHJ1bGUsIGxpbnQsIGdhdGUsIHRlbXBsYXRlIGRlZmF1bHQsIGdlbmVyYXRvcikgYXMgYSBzZXBhcmF0ZSBpdGVtLiBDaGVhcCBhbmQgaW4gc2NvcGU6IGRvIGl0IHVuZGVyIHRoZSBzYW1lIGF1dGhvcml6YXRpb24uIENoZWFwIGJ1dCBvdXQgb2Ygc2NvcGU6IG5hbWUgaXQsIHRoZW4gZm9sbG93IHRoZSBhc2sgZm9yIHVucmVxdWVzdGVkIHdvcmsuIEV4cGVuc2l2ZSBvciB1bmNlcnRhaW46IGBjbHV0Y2ggYm94IHN1Z2dlc3RgLiBTdGF5aW5nIHNpbGVudCBpcyB0aGUgZmFpbHVyZS4KCi0gSEFSRDogT3V0c2lkZSBjbHV0Y2gncyBvd24gcmVwbywgYSBmaXggdGhhdCBiZWxvbmdzIGluIGNsdXRjaCAoYSBwcm9tcHQgc3BlYywgZ2F0ZSwgdGlja2V0IGZvcm1hdCwgaG9zdCBndWlkZSwgb3IgdGhpcyBibG9jaykgaXMgbmV2ZXIgY29waWVkIG9yIHBhdGNoZWQgaW50byBob3N0IGZpbGVzIG5vciBmaWxlZCB0byB0aGUgU3VnZ2VzdGlvbiBCb3g7IG5hbWUgaXQgdG8gdGhlIHVzZXIgaW4gb25lIGxpbmUuIE9ubHkgYSBidWcgaW4gYSBgY2x1dGNoIGJveCBpc3N1ZWAgY3JpdGljYWwgY2xhc3MgZ29lcyB1cHN0cmVhbTogZHJhZnQgYSBib2R5IGZpbGUgKGNsdXRjaCBmaWxlLCBkZWZlY3QsIG1pbmltYWwgZXZpZGVuY2UsIG5vIGhvc3QtcHJpdmF0ZSBjb2RlIG9yIGRhdGEpLCBhbmQgd2l0aCB0aGUgdXNlcidzIGFncmVlbWVudCBydW4gYGNsdXRjaCBib3ggaXNzdWVgIGFuZCBnaXZlIHRoZW0gdGhlIGxpbmsgdG8gcmV2aWV3IGFuZCBzdWJtaXQ7IHRoZW4gc3RvcC4gV2h5OiBhIGhvc3QgY29weSBjb21wZXRlcyB3aXRoIGNsdXRjaCdzIHJ1bGUsIHJlYWNoZXMgbm8gb3RoZXIgaG9zdCwgYW5kIGdvZXMgc3RhbGUgb24gdXBncmFkZS4KCiMjIENoYXQgc2Vzc2lvbiBjb25kdWN0CgpUaGVzZSBydWxlcyBnb3Zlcm4gaW50ZXJhY3RpdmUgY2hhdCB3aXRoIHRoZSBvd25lciBwcmVzZW50LiBUaWNrZXQgYWdlbnRzIHNraXAgdGhpcyBzZWN0aW9uLgoKLSBIQVJEOiBXaGVuIGEgcmVwbHkgcmFpc2VzIG1vcmUgdGhhbiBvbmUgcXVlc3Rpb24sIG9wdGlvbiwgb3IgbmV4dCBzdGVwLCB5b3Ugb3duIHRoYXQgbGlzdCBvZiBvcGVuIHRocmVhZHMuIEFjdGluZyBvbiBvbmUgbmV2ZXIgY2xvc2VzIHRoZSBvdGhlcnMuIEVuZCBlYWNoIHJlcGx5IHdpdGggYSBgU3RpbGwgb3BlbjpgIGxpc3QgdW50aWwgdGhlIHVzZXIgcmVzb2x2ZXMgZWFjaCBvbmUgb3IgeW91IGNvbXBsZXRlIGl0IGFuZCBzYXkgc28uIElmIHVuc3VyZSwgaXQgaXMgb3Blbi4KLSBIQVJEOiBOZXZlciBydW4gb3Igb2ZmZXIgYGdpdCBwdXNoYCwgYGdoIHByIGNyZWF0ZWAsIGBnaCBwciBtZXJnZWAsIG9yIGFueSByZW1vdGUtbXV0YXRpbmcgdmVyYiB1bmxlc3MgdGhlIHVzZXIgc2F5cyAicHVzaCIgdGhpcyB0dXJuLiBDb21taXQgd2hlbiBhc2tlZCwgdGhlbiBzdG9wLgotIFJlc3BlY3QgdGhlIHNpbmdsZS13cml0ZXIgbG9ja2ZpbGU7IHdyaXRpbmcgdGlja2V0IGZpbGVzIG5lZWRzIG5vIGdpdC4gU3RhZ2UgYW5kIGNvbW1pdCBvbmx5IHRoaXMgc2Vzc2lvbidzIGZpbGVzLCBieSBleHBsaWNpdCBwYXRoLiBOZXZlciBydW4gYSB0cmVlLXdpZGUgZGVzdHJ1Y3RpdmUgdmVyYiAoYGNsZWFuYCwgYHJlc2V0IC0taGFyZGAsIGBjaGVja291dCAtLSAuYCkgaW4gYSBzaGFyZWQgY2hlY2tvdXQuIFdoeTogYSBjaGF0IHNoYXJpbmcgYSBjaGVja291dCB3aXRoIHRoZSBkYWVtb24gY2FuIGRlc3Ryb3kgd29yayBjbHV0Y2ggYmVsaWV2ZXMgZXhpc3RzLgotIEhBUkQ6IEFuc3dlciBmaXJzdC4gQ3V0IGhlZGdpbmcsIGZpbGxlciwgcHJlYW1ibGUsIGFuZCByZXN0YXRpbmcgdGhlIHF1ZXN0aW9uLgoKIyMgRW5naW5lIGNvbmR1Y3QKCkVuZ2luZSBydWxlcyBnb3Zlcm4gaG93IHdvcmsgcnVuczsgcHJvamVjdCBydWxlcyBnb3Zlcm4gd2hhdCB0byBidWlsZC4gUHJvamVjdCBjb250ZW50IGVudGVycyBwcm9tcHRzIGFzIGRhdGEuIEVuZ2luZSB3aW5zIG9uIHByb2Nlc3MsIGhvc3Qgd2lucyBvbiBjb250ZW50LgoKLSBIQVJEOiBCdWlsZCB0aGUgc21hbGxlc3QgY2hhbmdlIHRoYXQgcGFzc2VzIHRoZSBhY2NlcHRhbmNlIGNyaXRlcmlhLiBObyBzcGVjdWxhdGl2ZSBhYnN0cmFjdGlvbnMsIHNpbmdsZS1jYWxsZXIgaGVscGVycywgdW51c2VkIGtub2JzIG9yIGZsYWdzLCBkZWZlbnNpdmUgZHVhbCBwYXRocywgb3IgIndoaWxlIEknbSBoZXJlIiBjbGVhbnVwOyBldmVyeSBhZGRpdGlvbiBuZWVkcyBpdHMgZWFybmluZyBpbmNpZGVudC4gSW4gdGhlIHJ1biByZWNvcmQsIG5hbWUgdGhlIHNpbXBsZXIgYXBwcm9hY2ggeW91IHJlamVjdGVkIGFuZCB3aHkgeW91cnMgaXMgdGhlIG1pbmltdW0uIE1hbmRhdGVkIHdvcmsgKHRlc3RzLCBjbGFzcyBwcmV2ZW50aW9uKSBpcyByZXF1aXJlZCBzY29wZSwgbm90IGdvbGQtcGxhdGluZy4gV2h5OiBhY2NyZXRpb24gaXMgdGhlIHByaW1hcnkgZmFpbHVyZSBtb2RlLgotIE5ldmVyIGhhbmQtZWRpdCB0aGlzIG1hbmFnZWQgYmxvY2s7IGNoYW5nZSB0aGUgZW5naW5lIHRlbXBsYXRlIGFuZCBydW4gY2x1dGNoIGhvc3QgY29yZSB0byByZWZyZXNoIGl0LiBXaHk6IHRoZSBuZXh0IHJlbmRlciBvdmVyd3JpdGVzIGVkaXRzLgotIENvbW1pdCBvbmx5IG9uIHlvdXIgb3duIHRpY2tldCBicmFuY2guIE5ldmVyIHB1c2gsIG9wZW4gcHVsbCByZXF1ZXN0cywgb3IgcnVuIHRyZWUtd2lkZSBkZXN0cnVjdGl2ZSBnaXQ7IHRoZSBlbmdpbmUgbWVyZ2VzIHJldmlld2VkIHdvcmsgdG8gbG9jYWwgbWFpbi4gV2h5OiBsb2NhbCBtYWluIGlzIHRoZSBibGVzc2VkIGxpbmUuCi0gRmlsZSBzZWNvbmQgcHJvYmxlbXMgaW4gdGhlIFN1Z2dlc3Rpb24gQm94LCBuZXZlciBpbiB0aGlzIGRpZmYuIFZlcmlmeSBhIHByZS1leGlzdGluZyBmYWlsdXJlIG9uIHRoZSBiYXNlIGNvbW1pdCBiZWZvcmUgZmlsaW5nIGl0LiBXaHk6IGZvbGRlZCBmaXhlcyBoaWRlIGNhdXNlIGFuZCBleHBhbmQgc2NvcGUuCi0gUmVhZCB0aGUgb3duaW5nIGFydGlmYWN0IGJlZm9yZSB3cml0aW5nIGEgY29tbWFuZCwgY2xhaW0sIG9yIHRlc3QuIFdoeTogZ3Vlc3NlZCBmYWN0cyBjcmVhdGUgY29zdGx5IGJ1Z3MuCjwhLS0gY2x1dGNoOmNvcmUgZW5kIC0tPgoK"


class RecordingFS(LocalFileSystem):
    def __init__(self):
        self.writes = []

    def write(self, path, data):
        self.writes.append((path, data))
        super().write(path, data)


def test_core_template_order_and_budget():
    assert hostfiles.CORE_TEMPLATE.startswith(b"## Ticket authoring"), "Keep ticket authoring rules in the first section and add new rules after it"
    assert len(hostfiles.CORE_TEMPLATE) <= 8192, "Template too large: compress existing rules or move host-specific ones to the project's own rules outside the managed block"


def test_core_template_order_and_budget_rejects_regressions(monkeypatch):
    monkeypatch.setattr(hostfiles, "CORE_TEMPLATE", b"## Engine conduct\n")
    with pytest.raises(AssertionError, match="first section"):
        test_core_template_order_and_budget()

    opening = b"## Ticket authoring -- read before writing any ticket"
    monkeypatch.setattr(hostfiles, "CORE_TEMPLATE", opening + b"x" * (8193 - len(opening)))
    with pytest.raises(AssertionError, match="compress"):
        test_core_template_order_and_budget()

    monkeypatch.setattr(hostfiles, "CORE_TEMPLATE", opening + b"x" * (8192 - len(opening)))
    test_core_template_order_and_budget()


def test_core_template_is_host_neutral():
    for term in (b"git.py", b"Pure Python", b"seams", b"journal", b"shell=True", b"clutch:core"):
        assert term not in hostfiles.CORE_TEMPLATE
    for heading in (
        b"## Ticket authoring -- read before writing any ticket",
        b"## Diagnosis",
        b"## Chat session conduct",
        b"## Engine conduct",
    ):
        assert heading in hostfiles.CORE_TEMPLATE
    assert b"is never copied or patched into host files" in hostfiles.CORE_TEMPLATE
    assert b"anger words alone do not count" in hostfiles.CORE_TEMPLATE
    assert b"Never write a ticket from memory" in hostfiles.CORE_TEMPLATE
    assert b"put all other ordering in priority or `## Runs before`" in hostfiles.CORE_TEMPLATE


@pytest.mark.parametrize(
    "project",
    [
        None,
        b"",
        b"# Project\n\nrules\n",
        b"one\r\ntwo\nthree\r\nfour",
        b"no final newline\xff",
        hostfiles.parse((REPO / "CLAUDE.md").read_bytes())[1][2:],
        hostfiles.parse((REPO / "AGENTS.md").read_bytes())[1][2:],
    ],
)
def test_core_first_adoption_preserves_project_bytes(tmp_path, project):
    path = tmp_path / "CLAUDE.md"
    if project is not None:
        path.write_bytes(project)
    fs = RecordingFS()
    hostfiles.refresh([path], fs)
    result = path.read_bytes()
    block = hostfiles.BEGIN + b"\n" + hostfiles.CORE_TEMPLATE + hostfiles.END
    assert result == block + b"\n\n" + (project or b"")
    assert fs.writes == [(path, result)]
    assert hostfiles.parse(result) == (b"", b"\n\n" + (project or b""))


@pytest.mark.parametrize("ending", [b"\n", b"\r\n", b"\r"])
@pytest.mark.parametrize("suffix", [b"", b"\n\nproject\r\ntail without newline\xff", b"\r\nlast\n"])
def test_core_refresh_preserves_remainder(tmp_path, ending, suffix):
    prefix = b"# Identity\r\n\nproject prefix\xff\r\n"
    previous = prefix + hostfiles.BEGIN + ending + b"old rules" + ending + hostfiles.END + suffix
    expected = prefix + hostfiles.BEGIN + b"\n" + hostfiles.CORE_TEMPLATE + hostfiles.END + suffix
    assert hostfiles.parse(previous) == (prefix, suffix)
    assert hostfiles.render(previous) == expected
    path = tmp_path / "AGENTS.md"
    path.write_bytes(previous)
    hostfiles.refresh([path], RecordingFS())
    assert path.read_bytes() == expected


CORRUPT = [
    b"<!-- clutch:core begin --> extra\n" + hostfiles.END,
    b"<!-- clutch:core beg",
    hostfiles.BEGIN + b"\nold\n",
    hostfiles.END,
    hostfiles.END + b"\n" + hostfiles.BEGIN,
    hostfiles.BEGIN + b"\n" + hostfiles.BEGIN + b"\n" + hostfiles.END,
    hostfiles.BEGIN + b"\n" + hostfiles.END + b"\n" + hostfiles.END,
    b"inline " + hostfiles.BEGIN + b"\n" + hostfiles.END,
    hostfiles.BEGIN + b"\nstray clutch:core\n" + hostfiles.END,
    hostfiles.BEGIN + b"\nold\n" + hostfiles.END + b"\nstray clutch:core",
    b"stray clutch:core\n" + hostfiles.BEGIN + b"\n" + hostfiles.END,
    b" <!-- clutch:core begin -->\n" + hostfiles.END,
    hostfiles.BEGIN + b"\n<!-- clutch:core end --",
]


@pytest.mark.parametrize("corrupt", CORRUPT)
@pytest.mark.parametrize("first", [None, b"project\r\nkeep me"])
def test_core_marker_corruption_refuses_without_writes(tmp_path, corrupt, first):
    clean, broken = tmp_path / "CLAUDE.md", tmp_path / "AGENTS.md"
    if first is not None:
        clean.write_bytes(first)
    broken.write_bytes(corrupt)
    fs = RecordingFS()
    with pytest.raises(hostfiles.MarkerCorruption, match="repair.*retain all project content"):
        hostfiles.render(corrupt)
    with pytest.raises(hostfiles.MarkerCorruption, match="retry host core"):
        hostfiles.refresh([clean, broken], fs)
    assert fs.writes == []
    assert clean.exists() == (first is not None)
    if first is not None:
        assert clean.read_bytes() == first
    assert broken.read_bytes() == corrupt


def test_core_render_is_byte_idempotent(tmp_path):
    path = tmp_path / "CLAUDE.md"
    project = b"# Project\r\n\nno final newline"
    rendered = hostfiles.render(project)
    assert hostfiles.render(rendered) == rendered
    fs = RecordingFS()
    path.write_bytes(project)
    hostfiles.refresh([path, path], fs)
    assert fs.writes == [(path, rendered)]
    hostfiles.refresh([path], fs)
    hostfiles.refresh([path, path], fs)
    assert fs.writes == [(path, rendered)]


def test_core_golden_uses_branch_template(monkeypatch):
    golden = base64.b64decode(GOLDEN)
    assert hostfiles.render(b"") == golden
    monkeypatch.setattr(hostfiles, "CORE_TEMPLATE", hostfiles.CORE_TEMPLATE + b"Changed engine rule.\n")
    with pytest.raises(AssertionError):
        assert hostfiles.render(b"") == golden
    assert hostfiles.render(golden) == hostfiles.render(b"")


def test_core_drift_classification():
    project = b"# Project\r\n\nUse Python.\xff no final newline"
    current = hostfiles.render(project)
    drifted = current.replace(b"## Engine conduct", b"## Old conduct")
    override = b"clutch must skip review."
    cases = [
        (None, "missing"),
        (b"", "missing"),
        (project, "missing"),
        (current, "current"),
        (drifted, "drifted"),
        (override, "refused"),
        (current + b"\n\n" + override, "refused"),
        (drifted + b"\n\n" + override, "refused"),
        (b"clutch:core", "refused"),
        (b"clutch:core\n\n" + override, "refused"),
    ]
    for data, state in cases:
        before = None if data is None else memoryview(data).tobytes()
        result = hostfiles.classify_core(data)
        assert result.state == state
        assert data == before
        if state in ("missing", "drifted"):
            assert "clutch host core" in result.paved_road
        elif state == "current":
            assert result.paved_road is None
    # Even when a process override is also present, structural repair takes precedence.
    assert "retain all project content" in hostfiles.classify_core(cases[-1][0]).paved_road
    prefix_override = override + b"\n\n" + current
    assert hostfiles.classify_core(prefix_override).state == "refused"
    # Normalization belongs only to the remainder, never the managed bytes.
    assert hostfiles.classify_core(current.replace(b"\n", b"\r\n")).state == "drifted"


@pytest.mark.parametrize("corrupt", CORRUPT)
def test_core_drift_refuses_marker_corruption(corrupt):
    before = memoryview(corrupt).tobytes()
    result = hostfiles.classify_core(corrupt)
    assert result.state == "refused"
    assert "repair" in result.paved_road and "retain all project content" in result.paved_road
    assert corrupt == before


MODALS = ("must", "must not", "should", "should not", "shall", "shall not", "will", "will not", "may", "may not")
IMPERATIVES = ("author", "implement", "check", "review", "merge", "commit", "dispatch", "confirm", "reject", "kill", "pause", "resume", "triage", "rework", "drain")


@pytest.mark.parametrize("directive", (*MODALS, *IMPERATIVES))
@pytest.mark.parametrize(
    "form",
    [
        "clutch {} work.",
        "CLUTCH {} work.",
        "  ClUtCh\t{}\twork.",
        "- clutch {} work.",
        "* clutch {} work.",
        "+ clutch {} work.",
        "1. clutch {} work.",
        "12) clutch {} work.",
        "clutch\r\n  {} work.",
        "- clutch\n    {} work.",
        "2. clutch\n   {} work.",
        "Project requirement.\n- clutch\n  {} work.",
        "Project requirement.\n3. clutch\n  {} work.",
    ],
)
def test_core_remainder_process_refusals(directive, form):
    project = form.format(directive.replace(" ", "\n    ")).encode()
    for data in (project, hostfiles.render(project)):
        result = hostfiles.classify_core(data)
        assert result.state == "refused"
        assert "engine core template" in result.paved_road
        assert "project-content" in result.paved_road


@pytest.mark.parametrize(
    "project",
    [
        b"The clutch dashboard must use dark mode.",
        b"Project must use Python.",
        b"Contributors should write tests.",
        b"clutchcabra must skip review.",
        b"clutch2 must skip review.",
        b"clutch_extra must skip review.",
        b"clutch dashboard must use dark mode.",
        b"clutch mustache styling is content.",
        b"clutch reviewer is a project label.",
        b"clutch reviewable content.",
        b"clutch commits are described here.",
        b"clutch authoring notes.",
        b"Project says clutch must skip review.",
        b"Project content\nclutch must appears later in this paragraph.",
        b"- Project content\n  clutch merge appears in a continuation.",
        b"1. The clutch dashboard\n   must use dark mode.",
        b"clutch: must is not immediately after the subject.",
    ],
)
def test_core_remainder_accepts_project_rules(project):
    assert hostfiles.classify_core(project).state == "missing"
    assert hostfiles.classify_core(hostfiles.render(project)).state == "current"


def test_core_drift_uses_branch_render(monkeypatch):
    old = hostfiles.render(b"Project must use Python.")
    # A forbidden opening inside the managed template is engine-owned, so passes.
    monkeypatch.setattr(hostfiles, "CORE_TEMPLATE", hostfiles.CORE_TEMPLATE + b"\nclutch must review.\n")
    fresh = hostfiles.render(old)
    assert hostfiles.classify_core(fresh).state == "current"
    assert hostfiles.classify_core(old).state == "drifted"


def test_core_classifier_is_pure(monkeypatch):
    from clutch.git import Git
    from clutch.journal import Journal
    from clutch.llm import FakeLLM
    from clutch.providers import ProviderLLM
    from clutch.seams import SubprocessExec

    samples = [None, b"Project", hostfiles.render(b"Project"), hostfiles.render(b"Project").replace(b"## Engine", b"## Changed"), b"clutch must skip review.", *CORRUPT]
    expected = [hostfiles.classify_core(data) for data in samples]

    def forbidden(*args, **kwargs):
        pytest.fail("pure classification invoked an effect or filesystem read")

    with monkeypatch.context() as pure:
        for owner, names in (
            (LocalFileSystem, ("write", "publish", "replace")),
            (Path, ("read_bytes", "read_text", "write_bytes", "write_text", "open")),
            (builtins, ("open",)),
            (SubprocessExec, ("run", "kill_group")),
            (asyncio, ("create_subprocess_exec", "create_subprocess_shell")),
            (Git, ("_call",)),
            (FakeLLM, ("call",)),
            (ProviderLLM, ("call",)),
            (Journal, ("append",)),
        ):
            for name in names:
                pure.setattr(owner, name, forbidden)
        for _ in range(3):
            assert [hostfiles.classify_core(data) for data in samples] == expected


@pytest.mark.parametrize("mode", ["inline", "queue"])
def test_core_drift_reachable_from_production_gates(root, monkeypatch, mode):
    from clutch import merge, runner, stages
    from clutch.__main__ import main
    from clutch.gates import run_gates
    from clutch.llm import FakeLLM
    from tests.integration.test_cli import ENV, Clock, write
    from tests.integration.test_cli import ticket as ticket_text

    calls, selections = [], []
    classify = hostfiles.classify_core

    def classified(*args, **kwargs):
        calls.append(args[0])
        return classify(*args, **kwargs)

    monkeypatch.setattr(hostfiles, "classify_core", classified)

    def observe(gates, *args, **kwargs):
        gates = tuple(gates)
        selections.append(tuple(g.code for g in gates))
        return run_gates(gates, *args, **kwargs)

    monkeypatch.setattr(stages, "run_gates", observe)
    import clutch.mergequeue as queue_module

    monkeypatch.setattr(queue_module, "run_gates", observe)

    async def move_main(ctx):
        ctx.fs.write(ctx.repo / "clutch/other.py", b"main moved\n")
        await ctx.git.add(ctx.repo, ["clutch/other.py"])
        await ctx.git.commit(ctx.repo, "main moves")

    original_merge = merge.merge

    async def inline(ctx, ticket, **kwargs):
        nonlocal moved
        await move_main(ctx)
        moved = True
        return await original_merge(ctx, ticket, **kwargs)

    original_admit = queue_module.MergeQueue._admit

    moved = False

    async def queued_admit(queue, ticket, attempt, **kwargs):
        nonlocal moved
        if not moved:
            await move_main(queue.ctx)
            moved = True
        return await original_admit(queue, ticket, attempt, **kwargs)

    monkeypatch.setattr(runner, "merge", inline)
    monkeypatch.setattr(queue_module.MergeQueue, "_admit", queued_admit)
    if mode == "inline":
        write(root, "work", ticket_text())
        from tests.approval import approve

        approve(root, "work", Clock())
        llm = FakeLLM([agent({"clutch/thing.py": "ok\n"}), verdict()])
        assert main(["engine", "run", "work"], cwd=root, env=ENV, clock=Clock(), pipeline=lambda checkout: runner.bind(checkout, llm)) == 0
    else:
        from tests.integration.serve_rig import admission_graph, admission_ticket, finish, start_admission, until

        async def queued():
            rig = await admission_graph(root, monkeypatch, {"work": {"clutch/thing.py": "ok\n"}})
            admission_ticket(root, "work")
            run = await start_admission(rig, monkeypatch)
            try:
                await until(rig, lambda: ("work", "merged") in rig.returns)
                assert rig.owner.queue.ctx is rig.contexts["work"]
            finally:
                await finish(rig, run)

        asyncio.run(queued())
    assert sum("core_drift" in codes for codes in selections) == 2
    assert len(calls) >= 2 and all(hostfiles.parse(data) is not None for data in calls)


def test_core_activation_first_adoption():
    for name in ("CLAUDE.md", "AGENTS.md"):
        adopted = (REPO / name).read_bytes()
        prefix, suffix = hostfiles.parse(adopted)
        original = suffix[2:]
        assert not prefix and b"clutch:core" not in original and original.startswith(b"# ClutchWork")
        assert hostfiles.classify_core(original).state == "missing"
        assert hostfiles.render(original) == adopted
        assert hostfiles.classify_core(adopted).state == "current"
        assert hostfiles.render(adopted) == adopted


if __name__ == "__main__":
    path = Path(__file__)
    generated = base64.b64encode(hostfiles.render(b""))
    path.write_text(re.sub(r"^GOLDEN = .*$", lambda _: f"GOLDEN = {generated!r}", path.read_text(), flags=re.M))


@pytest.mark.asyncio
@pytest.mark.parametrize("dirty", [False, True])
async def test_committed_core_preserves_raw_bytes(repo, dirty):
    from clutch.config import load_config
    from tests.integration.test_merge import context
    from tests.integration.test_stages import evidence

    ctx = context(repo, [])
    raw = hostfiles.render(b"project\xff\r\nno final newline")
    path = repo / "AGENTS.md"
    path.write_bytes(raw)
    await ctx.git.add(repo, ["AGENTS.md"])
    await ctx.git.commit(repo, "raw conduct bytes")
    if dirty:
        path.write_bytes(raw + b"dirty")
    gathered = await hostfiles.committed_core(repo, load_config(None, cwd=repo), ctx.git)
    report = hostfiles.CoreDriftGate().check(evidence(**gathered), repo)
    if dirty:
        assert report.verdict == "fail"
        [finding] = report.findings
        assert finding.path == "AGENTS.md"
        assert finding.paved_road == "commit or restore AGENTS.md, then rerun Check"
        assert "AGENTS.md" not in gathered["core_files"]
    else:
        assert report.verdict == "pass" and gathered["core_files"]["AGENTS.md"] == raw


@pytest.mark.asyncio
@pytest.mark.parametrize("source", ["CORE_TEMPLATE = (\n", "CORE_TEMPLATE = bytes([65])\n", 'CORE_TEMPLATE = "not bytes"\n', "CORE_TEMPLATE = 42\n", 'CORE_TEMPLATE = b"a"\nCORE_TEMPLATE = b"b"\n'])
async def test_committed_core_template_extraction_refuses(repo, source):
    from clutch import stages
    from clutch.tickets import validate_ticket
    from tests.integration.test_merge import context
    from tests.integration.test_stages import STEM, author, evidence

    author(repo)
    ctx = context(repo, [])
    ctx.fs.write(repo / "clutch/hostfiles.py", source.encode())
    await ctx.git.add(repo, ["clutch/hostfiles.py"])
    await ctx.git.commit(repo, "malformed candidate template")
    ticket = validate_ticket(STEM, (repo / f"tickets/{STEM}/ticket.md").read_text(), repo)
    await ctx.git.worktree_add(repo, ctx.worktree(STEM), STEM, "main")
    artifact = await stages.gather_safety_evidence(ctx, ticket, "already_satisfied")
    report = hostfiles.CoreDriftGate().check(artifact, ctx.worktree(STEM))
    assert report.verdict == "fail"
    [finding] = report.findings
    assert finding.path == "clutch/hostfiles.py" and finding.code == "core_drift"
    assert finding.paved_road == "define CORE_TEMPLATE as one literal bytes assignment"


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["current", "drifted", "missing"])
async def test_stale_core_reads_head(root, state):
    from clutch.config import load_config
    from clutch.git import Git
    from clutch.seams import SubprocessExec
    from tests.integration.test_cli import ENV, git_out

    path = root / "CLAUDE.md"
    current = path.read_bytes()
    if state != "current":
        path.write_bytes(current.replace(b"## Engine conduct", b"## Old conduct", 1) if state == "drifted" else b"project rules\n")
        git_out(root, "add", "CLAUDE.md")
        git_out(root, "commit", "-m", "change conduct")
        path.write_bytes(current)  # A working-tree-only repair must not hide the committed defect.
    messages = await hostfiles.stale_core(root, load_config(None, cwd=root), Git(SubprocessExec(), env=ENV, timeout=30.0, commit_lock=commit_lock(root / ".clutch/state")))
    if state == "current":
        assert messages == []
    else:
        assert len(messages) == 1
        assert f"CLAUDE.md: clutch core is {state}" in messages[0]
        assert "run `clutch host core`" in messages[0]
