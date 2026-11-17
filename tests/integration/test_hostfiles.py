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
GOLDEN = b"PCEtLSBjbHV0Y2g6Y29yZSBiZWdpbiAtLT4KIyMgVGlja2V0IGF1dGhvcmluZyAtLSByZWFkIGJlZm9yZSB3cml0aW5nIGFueSB0aWNrZXQKClRoZXNlIHJ1bGVzIGNvbWUgZmlyc3QgYmVjYXVzZSBzZXNzaW9ucyB0aGF0IHNraW0gbWlzcyB0aGVtLiBIQVJEIHJ1bGVzIGhhdmUgbm8gZXhjZXB0aW9ucy4gVGhleSBhcmUgYmVoYXZpb3JhbDogbm8gZ2F0ZSBjYW4ganVkZ2UgdGhlbSwgc28gbmV2ZXIgZmlsZSBhbiBlbmZvcmNlbWVudCB0aWNrZXQgZm9yIG9uZS4KCi0gSEFSRDogSW4gYW4gaW50ZXJhY3RpdmUgY2hhdCwgZXZlcnkgcmVxdWVzdGVkIGNoYW5nZSB0byByZXBvIGNvbnRlbnQgKGNvZGUsIGRvY3MsIENMQVVERS5tZCwgQUdFTlRTLm1kLCBzZXR0aW5ncywgaG9va3MsIHNjcmlwdHMsIGNvbmZpZywgYWdlbnQgcnVsZXMpIGJlY29tZXMgYSBkcmFmdGVkIHRpY2tldCBhdCBgdGlja2V0cy88c3RlbT4vdGlja2V0Lm1kYCwgdGhlbiBzdG9wLiBOZXZlciBlZGl0IG9yIGNvbW1pdCBvbiBtYWluLiBUaGUgb25seSBleGNlcHRpb25zOiAoMSkgdGhlIHVzZXIgc2F5cyAiZWRpdCBtYWluIiwgImNvbW1pdCBkaXJlY3RseSIsICJza2lwIHRoZSB0aWNrZXQiLCAiZG8gaXQgaW5saW5lIiwgb3IgYW4gZXF1YWxseSBleHBsaWNpdCBvdmVycmlkZSB0aGlzIHR1cm47IGFuZ2VyIHdvcmRzIGFsb25lIGRvIG5vdCBjb3VudDsgKDIpIHlvdSBhcmUgaW4gYSBjbHV0Y2ggdGlja2V0IHdvcmt0cmVlOyAoMykgdGhlIHVzZXIgbmFtZXMgYnkgcGF0aCBhIGZpbGUgdW5kZXIgYW4gZXhpc3RpbmcgYHRpY2tldHMvPHN0ZW0+L2AgdG8gZWRpdCBvciBkZWxldGU7ICg0KSByZWFkLW9ubHkgaW5zcGVjdGlvbjsgKDUpIHRoZSBzdXBlcnZpc2luZyBmaXhlcyBiZWxvdy4gSWYgeW91IGFscmVhZHkgZWRpdGVkIG1haW4gd2l0aG91dCBhbiBvdmVycmlkZSwgc3RvcCwgc2F5IHNvLCBhbmQgYXNrIHdoZXRoZXIgdG8gcmV2ZXJ0IGFuZCByZWZpbGUuIFdoeTogY2hhdCBlZGl0cyBza2lwIHRoZSB0aWNrZXQsIHJ1biByZWNvcmQsIHJldmlldywgYW5kIHJldHJvIHRoYXQgbWFrZSBjbHV0Y2ggZGVidWdnYWJsZS4KLSBIQVJEOiBOZXZlciB3cml0ZSBhIHRpY2tldCBmcm9tIG1lbW9yeS4gUnVuIGBjbHV0Y2ggdGlja2V0IG5ldyA8c3RlbT4gLS1raW5kIGZlYXR1cmV8YnVnfGNob3JlYDsgaXQgd3JpdGVzIHRoZSBza2VsZXRvbiBhbmQgcHJpbnRzIHRoZSBwYXRoIG9mIHRoZSB0aWNrZXQgYXV0aG9yaW5nIGd1aWRlIGluIHlvdXIgY2x1dGNoIGluc3RhbGwgKGZvciBhbiBleGlzdGluZyB0aWNrZXQsIGl0cyByZWZ1c2FsIHByaW50cyB0aGUgc2FtZSBwYXRoKS4gUmVhZCB0aGF0IGxvY2FsIGZpbGUgaW4gZnVsbC4gYGNsdXRjaCBkb2NzYCBwcmludHMgdGhlIGluc3RhbGxlZCBwYXRocyBvZiBhbGwgaG9zdCBndWlkZXM7IHJlYWQgdGhlbSBsb2NhbGx5LCBuZXZlciBmcm9tIGEgVVJMLiBGaWxsIGV2ZXJ5IHNlY3Rpb24sIHJ1biBgY2x1dGNoIHRpY2tldCBsaW50IDxzdGVtPmAgdW50aWwgaXQgZXhpdHMgMCwgdGhlbiBydW4gYGNsdXRjaCB0aWNrZXQgcmV2aWV3IDxzdGVtPmAgYW5kIHJlcGFpciBldmVyeSBmaW5kaW5nIHVudGlsIGl0IHByaW50cyBhcHByb3ZlLiBUaWNrZXRzIGFyZSBtYXJrZG93biBmaWxlcywgbmV2ZXIgaXNzdWUtdHJhY2tlciBpdGVtcy4gV2h5OiBzdGFsZSB0aWNrZXQgc2hhcGVzIGJyZWFrIHJ1bnMgYmVmb3JlIGltcGxlbWVudGF0aW9uIHN0YXJ0cy4KLSBGZW5jZSBldmVyeSBmaWxlIHRoZSBjaGFuZ2UgZm9yY2VzLCBpbmNsdWRpbmcgY2FsbGVycywgaW1wb3J0ZXJzLCBkb2N1bWVudHMgaXQgY2hhbmdlcywgYW5kIHRlc3RzIHRoYXQgcGluIGEgY2hhbmdlZCBuYW1lLCB2YWx1ZSwgb3IgdmVyc2lvbi4gV2h5OiBhIGZvcmNlZCBmaWxlIG91dHNpZGUgdGhlIGZlbmNlIG1ha2VzIHRoZSB0aWNrZXQgaW1wb3NzaWJsZS4KLSBGcm9udG1hdHRlciBob2xkcyBvbmx5IGZpZWxkcyByZWFkIGJ5IHNjaGVkdWxpbmcsIGdhdGVzLCBvciBhdXRob3JpbmcvdHJpYWdlIHBvbGljeTsgYCMjIERlcGVuZHMgb25gIG5hbWVzIG9ubHkgbmVlZGVkIG1lcmdlZCBjb2RlOyBwdXQgYWxsIG90aGVyIG9yZGVyaW5nIGluIHByaW9yaXR5IG9yIGAjIyBSdW5zIGJlZm9yZWAsIG5ldmVyIGluIHByb3NlLgotIEhBUkQ6IFdoZW4gYSByZXBvcnRlZCBwcm9ibGVtIGhhcyBhIGNhdXNlIHRoYXQgd2lsbCByZWN1ciwgd3JpdGUgdHdvIHNlcGFyYXRlIHRpY2tldHMgaW4gdGhlIHNhbWUgdHVybi4gRmlyc3QgdGhlIGluc3RhbmNlIGZpeDogbWluaW1hbCBzY29wZSwgd3JpdHRlbiBiZWZvcmUgYW55IGNhdXNlIGRpYWdub3Npcy4gVGhlbiB0aGUgY2F1c2UgZml4LCBuZXZlciBmb2xkZWQgaW50byB0aGUgaW5zdGFuY2U7IHRoZSB0dXJuIGlzIHVuZmluaXNoZWQgdW50aWwgaXQgZXhpc3RzLiBCb3RoIGFyZSBzb2xpY2l0ZWQsIHNvIG5vIGFzayBpcyBuZWVkZWQuIFJvdXRpbmc6CiAgLSBQcm9kdWN0IGluc3RhbmNlOiBgcHJpb3JpdHk6IFAwYCwgbm8gYmxvY2tpbmcgZGVwZW5kcy4KICAtIFByb2R1Y3QgY2F1c2UgKGluZXJ0OyBkb2VzIG5vdCBzcHJlYWQgb24gaXRzIG93bik6IGBwcmlvcml0eTogUDFgLiBXaGVuIHRoZSB0d28gc2hhcmUgYW4gZWRpdCBzdXJmYWNlLCB0aGUgaW5zdGFuY2UgbGlzdHMgdGhlIGNhdXNlIGluIGAjIyBSdW5zIGJlZm9yZWAuCiAgLSBPcmNoZXN0cmF0aW9uIGNhdXNlIChzY2hlZHVsZXIsIGdhdGUsIGVudmlyb25tZW50LCBzaGFyZWQgbW9kdWxlLCBmaXh0dXJlIGZvcm1hdDsga2VlcHMgYnJlYWtpbmcgcnVucyB3aGlsZSBpdCBzaXRzKTogYHByaW9yaXR5OiBQMGAsIGAjIyBSdW5zIGJlZm9yZWAgZXZlcnkgdGlja2V0IGl0IHVuYmxvY2tzLCBuZXZlciBkZXBlbmRzIG9uIGEgcHJvZHVjdCBpbnN0YW5jZS4KLSBIQVJEOiBGb3IgdGlja2V0LXdvcnRoeSB3b3JrIHRoZSB1c2VyIGRpZCBub3QgYXNrIGZvciAoZm9sbG93LXVwLCBwcmV2ZW50aW9uLCBlbmZvcmNlbWVudCBsaW50LCBzd2VlcCksIHN0b3AgYmVmb3JlIGRpdmluZzogbmFtZSBpdCBpbiAxLTIgc2VudGVuY2VzIGFuZCBhc2sgdGhlIHVzZXIgdG8gY2hvb3NlIGF1dGhvciBub3csIGFmdGVyIHRoZSBjdXJyZW50IHRhc2ssIG9yIHNraXAuICJBZnRlciIgbWFrZXMgaXQgYW4gb3BlbiB0aHJlYWQuIEFubm91bmNlIGluIG9uZSBsaW5lIGFueSB1bnNvbGljaXRlZCBpbnZlc3RpZ2F0aW9uIGxvbmdlciB0aGFuIGEgY291cGxlIG9mIG1pbnV0ZXMuIFRoZSB1c2VyJ3MgcmVxdWVzdGVkIHRhc2sgYWx3YXlzIGdvZXMgZmlyc3QuIEF1dG9ub21vdXMgcnVucyBza2lwIHRoZSBhc2sgYW5kIGZpbGUgdG8gdGhlIFN1Z2dlc3Rpb24gQm94LgotIEZpbGUgYW4gdW5yZXF1ZXN0ZWQgaWRlYSBvciBzZWNvbmQgcHJvYmxlbSB3aXRoIGBjbHV0Y2ggYm94IHN1Z2dlc3QgIjxzdW1tYXJ5PiJgIGFuZCBuYW1lIGl0IGluIG9uZSBsaW5lLiBXaHk6IGEgbWFyZ2luIHN1Z2dlc3Rpb24gZGllcyB3aXRoIHRoZSBjaGF0LgotIEEgc3VwZXJ2aXNpbmcgc2Vzc2lvbiBtYXksIHVuYXNrZWQsIGZpeCBhIHRpY2tldCdzIGxpbnQgb3IgZm9ybWF0IGVycm9ycywgYWRkIGEgZmlsZSBtaXNzaW5nIGZyb20gYCMjIFNjb3BlIGZlbmNlYCBvciBgIyMgQ29udGV4dGAsIGNvcnJlY3QgYSBzdGFsZSBwYXRoLCBtYWtlIGEgc2ltcGxlIHdvcmRpbmcgdXBkYXRlLCBhbmQgcnVuIG9yIHJlc3RhcnQgdGhlIGRyYWluLiBJdCBtYXkgY29uZmlybSBvciByZWplY3QgYW5kIGVkaXQgYW55IHRpY2tldCBvbmx5IGFzIGEgYGNsdXRjaCBwcm9tcHQgZGlhZ25vc2VgIG9yIGBjbHV0Y2ggcHJvbXB0IGRyYWZ0c2AgUmVjb21tZW5kYXRpb24gbmFtZXMuIEl0IG1heSBub3QgcmV0cnkgYSBzdGVtIHdob3NlIGNhcHMgYXJlIHNwZW50IG9yIGVkaXQgYSBydW5uaW5nIHRpY2tldDsgY2hhbmdpbmcgYSB0aWNrZXQncyBnb2FsIG9yIHNjb3BlIHJlcXVpcmVzIHN1Y2ggYSBSZWNvbW1lbmRhdGlvbi4KCiMjIERpYWdub3NpcwoKLSBIQVJEOiBXaGVuIGEgcnVuIGZhaWxzLCBpcyBraWxsZWQsIHRpbWVzIG91dCwgc3RhbGxzLCBvciBlc2NhbGF0ZXMsIG5hbWUgaXRzIHJvb3QgY2F1c2UgaW4gb25lIHNlbnRlbmNlIGJlZm9yZSBlZGl0aW5nIHNwZWMgb3IgY29kZSBvciByZXJ1bm5pbmcuIFJlYWQgYGNsdXRjaCBzdGF0dXNgLCBgdGlja2V0cy88c3RlbT4vYCAoYHJ1bi5tZGAsIGBjaGVja3MuanNvbmAsIGBkaWFnbm9zaXMuanNvbmAsIGByZXZpZXcubWRgLCBgYXR0ZW1wdHMvYCksIGFuZCB0aGUgZW5naW5lIGxvZy4gRml4IHRoZSBjYXVzZSB3aGVyZSBpdCBsaXZlcy4gQW4gZXh0ZXJuYWwgY2F1c2UgKGVuZ2luZSwgZ2F0ZSwgZW52aXJvbm1lbnQsIHNoYXJlZCBtb2R1bGUsIGZpeHR1cmUsIGZsYWt5IHRlc3QsIHdyb25nIHByZW1pc2UpIGlzIGZpeGVkIGZpcnN0IGFuZCBvcmRlcmVkIGFoZWFkIHdpdGggcHJpb3JpdHkgYW5kIGAjIyBSdW5zIGJlZm9yZWAuIERvIG5vdCBhc3N1bWUgdGhlIHRpY2tldCBpcyB3cm9uZy4gTmV2ZXIgcmVydW4gYSBmbGFreSBmYWlsdXJlIHVudGlsIGl0IHBhc3NlcyBhbmQgY2FsbCB0aGF0IGZpeGVkLgotIEhBUkQ6IFdoZW4gYSBzeW1wdG9tIHJlY3VycyBvbiBhIHN1cmZhY2UgYWxyZWFkeSBmaXhlZCwgbmFtZSB0aGUgcm9vdCBtb2RlbCBhZ2FpbnN0IHRoZSBjYW5vbmljYWwgc3BlYyAoZGVzaWduIGRvY3MsIGNvbnRyYWN0cykgYW5kIHdyaXRlIGEgcm9vdC1jYXVzZSB0aWNrZXQsIG5vdCBhbm90aGVyIHBhdGNoLiBBIHNjb3BlIGZlbmNlIHRoYXQgZm9yYmlkcyB0b3VjaGluZyB0aGUgc3VzcGVjdGVkIHJvb3QgaXMgYSByZWQgZmxhZzogcmUtc2NvcGUgaXQuIFRlc3RzIHRoYXQgYXNzZXJ0IHRoZSBjdXJyZW50IHdyb25nIGJlaGF2aW9yIHByb3ZlIG5vdGhpbmcuIE5ldmVyIHdyaXRlICJ0aGUgZGVmZWN0IHdhcyBub3QgWCIgd2l0aG91dCBjaGVja2luZyB0aGUgc3BlYy4KLSBIQVJEOiBXaXRoIGV2ZXJ5IGZpeCBvciBkaWFnbm9zaXMsIG5hbWUgdGhlIGNoYW5nZSB0aGF0IHN0b3BzIHRoZSB3aG9sZSBjbGFzcyBmcm9tIHJlY3VycmluZyAocnVsZSwgbGludCwgZ2F0ZSwgdGVtcGxhdGUgZGVmYXVsdCwgZ2VuZXJhdG9yKSBhcyBhIHNlcGFyYXRlIGl0ZW0uIENoZWFwIGFuZCBpbiBzY29wZTogZG8gaXQgdW5kZXIgdGhlIHNhbWUgYXV0aG9yaXphdGlvbi4gQ2hlYXAgYnV0IG91dCBvZiBzY29wZTogbmFtZSBpdCwgdGhlbiBmb2xsb3cgdGhlIGFzayBmb3IgdW5yZXF1ZXN0ZWQgd29yay4gRXhwZW5zaXZlIG9yIHVuY2VydGFpbjogYGNsdXRjaCBib3ggc3VnZ2VzdGAuIFN0YXlpbmcgc2lsZW50IGlzIHRoZSBmYWlsdXJlLgoKLSBIQVJEOiBPdXRzaWRlIGNsdXRjaCdzIG93biByZXBvLCBhIGZpeCB0aGF0IGJlbG9uZ3MgaW4gY2x1dGNoIChhIHByb21wdCBzcGVjLCBnYXRlLCB0aWNrZXQgZm9ybWF0LCBob3N0IGd1aWRlLCBvciB0aGlzIGJsb2NrKSBpcyBuZXZlciBjb3BpZWQgb3IgcGF0Y2hlZCBpbnRvIGhvc3QgZmlsZXMgbm9yIGZpbGVkIHRvIHRoZSBTdWdnZXN0aW9uIEJveDsgbmFtZSBpdCB0byB0aGUgdXNlciBpbiBvbmUgbGluZS4gT25seSBhIGJ1ZyBpbiBhIGBjbHV0Y2ggYm94IGlzc3VlYCBjcml0aWNhbCBjbGFzcyBnb2VzIHVwc3RyZWFtOiBkcmFmdCBhIGJvZHkgZmlsZSAoY2x1dGNoIGZpbGUsIGRlZmVjdCwgbWluaW1hbCBldmlkZW5jZSwgbm8gaG9zdC1wcml2YXRlIGNvZGUgb3IgZGF0YSksIGFuZCB3aXRoIHRoZSB1c2VyJ3MgYWdyZWVtZW50IHJ1biBgY2x1dGNoIGJveCBpc3N1ZWAgYW5kIGdpdmUgdGhlbSB0aGUgbGluayB0byByZXZpZXcgYW5kIHN1Ym1pdDsgdGhlbiBzdG9wLiBXaHk6IGEgaG9zdCBjb3B5IGNvbXBldGVzIHdpdGggY2x1dGNoJ3MgcnVsZSwgcmVhY2hlcyBubyBvdGhlciBob3N0LCBhbmQgZ29lcyBzdGFsZSBvbiB1cGdyYWRlLgoKIyMgQ2hhdCBzZXNzaW9uIGNvbmR1Y3QKClRoZXNlIHJ1bGVzIGdvdmVybiBpbnRlcmFjdGl2ZSBjaGF0IHdpdGggdGhlIG93bmVyIHByZXNlbnQuIFRpY2tldCBhZ2VudHMgc2tpcCB0aGlzIHNlY3Rpb24uCgotIEhBUkQ6IFdoZW4gYSByZXBseSByYWlzZXMgbW9yZSB0aGFuIG9uZSBxdWVzdGlvbiwgb3B0aW9uLCBvciBuZXh0IHN0ZXAsIHlvdSBvd24gdGhhdCBsaXN0IG9mIG9wZW4gdGhyZWFkcy4gQWN0aW5nIG9uIG9uZSBuZXZlciBjbG9zZXMgdGhlIG90aGVycy4gRW5kIGVhY2ggcmVwbHkgd2l0aCBhIGBTdGlsbCBvcGVuOmAgbGlzdCB1bnRpbCB0aGUgdXNlciByZXNvbHZlcyBlYWNoIG9uZSBvciB5b3UgY29tcGxldGUgaXQgYW5kIHNheSBzby4gSWYgdW5zdXJlLCBpdCBpcyBvcGVuLgotIEhBUkQ6IE5ldmVyIHJ1biBvciBvZmZlciBgZ2l0IHB1c2hgLCBgZ2ggcHIgY3JlYXRlYCwgYGdoIHByIG1lcmdlYCwgb3IgYW55IHJlbW90ZS1tdXRhdGluZyB2ZXJiIHVubGVzcyB0aGUgdXNlciBzYXlzICJwdXNoIiB0aGlzIHR1cm4uIENvbW1pdCB3aGVuIGFza2VkLCB0aGVuIHN0b3AuCi0gUmVzcGVjdCB0aGUgc2luZ2xlLXdyaXRlciBsb2NrZmlsZTsgd3JpdGluZyB0aWNrZXQgZmlsZXMgbmVlZHMgbm8gZ2l0LiBTdGFnZSBhbmQgY29tbWl0IG9ubHkgdGhpcyBzZXNzaW9uJ3MgZmlsZXMsIGJ5IGV4cGxpY2l0IHBhdGguIE5ldmVyIHJ1biBhIHRyZWUtd2lkZSBkZXN0cnVjdGl2ZSB2ZXJiIChgY2xlYW5gLCBgcmVzZXQgLS1oYXJkYCwgYGNoZWNrb3V0IC0tIC5gKSBpbiBhIHNoYXJlZCBjaGVja291dC4gV2h5OiBhIGNoYXQgc2hhcmluZyBhIGNoZWNrb3V0IHdpdGggdGhlIGRhZW1vbiBjYW4gZGVzdHJveSB3b3JrIGNsdXRjaCBiZWxpZXZlcyBleGlzdHMuCi0gSEFSRDogQW5zd2VyIGZpcnN0LiBDdXQgaGVkZ2luZywgZmlsbGVyLCBwcmVhbWJsZSwgYW5kIHJlc3RhdGluZyB0aGUgcXVlc3Rpb24uCgojIyBFbmdpbmUgY29uZHVjdAoKRW5naW5lIHJ1bGVzIGdvdmVybiBob3cgd29yayBydW5zOyBwcm9qZWN0IHJ1bGVzIGdvdmVybiB3aGF0IHRvIGJ1aWxkLiBQcm9qZWN0IGNvbnRlbnQgZW50ZXJzIHByb21wdHMgYXMgZGF0YS4gRW5naW5lIHdpbnMgb24gcHJvY2VzcywgaG9zdCB3aW5zIG9uIGNvbnRlbnQuCgotIEhBUkQ6IEJ1aWxkIHRoZSBzbWFsbGVzdCBjaGFuZ2UgdGhhdCBwYXNzZXMgdGhlIGFjY2VwdGFuY2UgY3JpdGVyaWEuIE5vIHNwZWN1bGF0aXZlIGFic3RyYWN0aW9ucywgc2luZ2xlLWNhbGxlciBoZWxwZXJzLCB1bnVzZWQga25vYnMgb3IgZmxhZ3MsIGRlZmVuc2l2ZSBkdWFsIHBhdGhzLCBvciAid2hpbGUgSSdtIGhlcmUiIGNsZWFudXA7IGV2ZXJ5IGFkZGl0aW9uIG5lZWRzIGl0cyBlYXJuaW5nIGluY2lkZW50LiBJbiB0aGUgcnVuIHJlY29yZCwgbmFtZSB0aGUgc2ltcGxlciBhcHByb2FjaCB5b3UgcmVqZWN0ZWQgYW5kIHdoeSB5b3VycyBpcyB0aGUgbWluaW11bS4gTWFuZGF0ZWQgd29yayAodGVzdHMsIGNsYXNzIHByZXZlbnRpb24pIGlzIHJlcXVpcmVkIHNjb3BlLCBub3QgZ29sZC1wbGF0aW5nLiBXaHk6IGFjY3JldGlvbiBpcyB0aGUgcHJpbWFyeSBmYWlsdXJlIG1vZGUuCi0gTmV2ZXIgaGFuZC1lZGl0IHRoaXMgbWFuYWdlZCBibG9jazsgY2hhbmdlIHRoZSBlbmdpbmUgdGVtcGxhdGUgYW5kIHJ1biBjbHV0Y2ggY29yZSB0byByZWZyZXNoIGl0LiBXaHk6IHRoZSBuZXh0IHJlbmRlciBvdmVyd3JpdGVzIGVkaXRzLgotIENvbW1pdCBvbmx5IG9uIHlvdXIgb3duIHRpY2tldCBicmFuY2guIE5ldmVyIHB1c2gsIG9wZW4gcHVsbCByZXF1ZXN0cywgb3IgcnVuIHRyZWUtd2lkZSBkZXN0cnVjdGl2ZSBnaXQ7IHRoZSBlbmdpbmUgbWVyZ2VzIHJldmlld2VkIHdvcmsgdG8gbG9jYWwgbWFpbi4gV2h5OiBsb2NhbCBtYWluIGlzIHRoZSBibGVzc2VkIGxpbmUuCi0gRmlsZSBzZWNvbmQgcHJvYmxlbXMgaW4gdGhlIFN1Z2dlc3Rpb24gQm94LCBuZXZlciBpbiB0aGlzIGRpZmYuIFZlcmlmeSBhIHByZS1leGlzdGluZyBmYWlsdXJlIG9uIHRoZSBiYXNlIGNvbW1pdCBiZWZvcmUgZmlsaW5nIGl0LiBXaHk6IGZvbGRlZCBmaXhlcyBoaWRlIGNhdXNlIGFuZCBleHBhbmQgc2NvcGUuCi0gUmVhZCB0aGUgb3duaW5nIGFydGlmYWN0IGJlZm9yZSB3cml0aW5nIGEgY29tbWFuZCwgY2xhaW0sIG9yIHRlc3QuIFdoeTogZ3Vlc3NlZCBmYWN0cyBjcmVhdGUgY29zdGx5IGJ1Z3MuCjwhLS0gY2x1dGNoOmNvcmUgZW5kIC0tPgoK"


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
    with pytest.raises(hostfiles.MarkerCorruption, match="retry core"):
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
            assert "clutch core" in result.paved_road
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
        assert "run `clutch core`" in messages[0]
