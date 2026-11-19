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
GOLDEN = b"PCEtLSBjbHV0Y2g6Y29yZSBiZWdpbiAtLT4KIyMgVGlja2V0IGF1dGhvcmluZyAtLSByZWFkIGJlZm9yZSB3cml0aW5nIGFueSB0aWNrZXQKCkhBUkQgcnVsZXMgaGF2ZSBubyBleGNlcHRpb25zLiBUaGVzZSBydWxlcyBjYW5ub3QgYmUgZ2F0ZWQ7IG5ldmVyIGZpbGUgYW4gZW5mb3JjZW1lbnQgdGlja2V0IGZvciBvbmUuCgotIEhBUkQ6IEluIGFuIGludGVyYWN0aXZlIGNoYXQsIGV2ZXJ5IHJlcXVlc3RlZCBjaGFuZ2UgdG8gcmVwbyBjb250ZW50IChjb2RlLCBkb2NzLCBDTEFVREUubWQsIEFHRU5UUy5tZCwgc2V0dGluZ3MsIGhvb2tzLCBzY3JpcHRzLCBjb25maWcsIGFnZW50IHJ1bGVzKSBiZWNvbWVzIGEgZHJhZnRlZCB0aWNrZXQgYXQgYHRpY2tldHMvPHN0ZW0+L3RpY2tldC5tZGAsIHRoZW4gc3RvcC4gTmV2ZXIgZWRpdCBvciBjb21taXQgb24gbWFpbi4gVGhlIG9ubHkgZXhjZXB0aW9uczogKDEpIHRoZSB1c2VyIHNheXMgImVkaXQgbWFpbiIsICJjb21taXQgZGlyZWN0bHkiLCAic2tpcCB0aGUgdGlja2V0IiwgImRvIGl0IGlubGluZSIsIG9yIGFuIGVxdWFsbHkgZXhwbGljaXQgb3ZlcnJpZGUgdGhpcyB0dXJuOyBhbmdlciB3b3JkcyBhbG9uZSBkbyBub3QgY291bnQ7ICgyKSB5b3UgYXJlIGluIGEgY2x1dGNoIHRpY2tldCB3b3JrdHJlZTsgKDMpIHRoZSB1c2VyIG5hbWVzIGJ5IHBhdGggYSBmaWxlIHVuZGVyIGFuIGV4aXN0aW5nIGB0aWNrZXRzLzxzdGVtPi9gIHRvIGVkaXQgb3IgZGVsZXRlOyAoNCkgcmVhZC1vbmx5IGluc3BlY3Rpb247ICg1KSB0aGUgc3VwZXJ2aXNpbmcgZml4ZXMgYmVsb3cuIElmIHlvdSBhbHJlYWR5IGVkaXRlZCBtYWluIHdpdGhvdXQgYW4gb3ZlcnJpZGUsIHN0b3AsIHNheSBzbywgYW5kIGFzayB3aGV0aGVyIHRvIHJldmVydCBhbmQgcmVmaWxlLiBXaHk6IGNoYXQgZWRpdHMgc2tpcCB0aGUgdGlja2V0LCBydW4gcmVjb3JkLCByZXZpZXcsIGFuZCByZXRybyB0aGF0IG1ha2UgY2x1dGNoIGRlYnVnZ2FibGUuCi0gSEFSRDogTmV2ZXIgd3JpdGUgYSB0aWNrZXQgZnJvbSBtZW1vcnkuIFJ1biBgY2x1dGNoIHRpY2tldCBuZXcgPHN0ZW0+IC0ta2luZCBmZWF0dXJlfGJ1Z3xjaG9yZWA7IGl0IHdyaXRlcyB0aGUgc2tlbGV0b24gYW5kIHByaW50cyB0aGUgcGF0aCBvZiB0aGUgdGlja2V0IGF1dGhvcmluZyBndWlkZSBpbiB5b3VyIGNsdXRjaCBpbnN0YWxsIChmb3IgYW4gZXhpc3RpbmcgdGlja2V0LCBpdHMgcmVmdXNhbCBwcmludHMgdGhlIHNhbWUgcGF0aCkuIFJlYWQgdGhhdCBsb2NhbCBmaWxlIGluIGZ1bGwuIGBjbHV0Y2ggaG9zdCBkb2NzYCBwcmludHMgdGhlIGluc3RhbGxlZCBwYXRocyBvZiBhbGwgaG9zdCBndWlkZXM7IHJlYWQgdGhlbSBsb2NhbGx5LCBuZXZlciBmcm9tIGEgVVJMLiBGaWxsIGV2ZXJ5IHNlY3Rpb24sIHJ1biBgY2x1dGNoIHRpY2tldCBsaW50IDxzdGVtPmAgdW50aWwgaXQgZXhpdHMgMCwgdGhlbiBydW4gYGNsdXRjaCB0aWNrZXQgcmV2aWV3IDxzdGVtPmAgYW5kIHJlcGFpciBldmVyeSBmaW5kaW5nIHVudGlsIGl0IHByaW50cyBhcHByb3ZlLiBUaWNrZXRzIGFyZSBtYXJrZG93biBmaWxlcywgbmV2ZXIgaXNzdWUtdHJhY2tlciBpdGVtcy4gV2h5OiBzdGFsZSB0aWNrZXQgc2hhcGVzIGJyZWFrIHJ1bnMgYmVmb3JlIGltcGxlbWVudGF0aW9uIHN0YXJ0cy4KLSBEZWNsYXJlIGVhY2ggYm91bmRhcnkgZGlzcG9zaXRpb24sIHJldXNlIGl0cyBjYW5vbmljYWwgb3duZXIsIGp1c3RpZnkgYSBuZXcgb3duZXIsIGFuZCBuZXZlciBpbnZlbnQgYW4gdW5kZWNsYXJlZCBib3VuZGFyeS4KLSBGZW5jZSBldmVyeSBmaWxlIHRoZSBjaGFuZ2UgZm9yY2VzLCBpbmNsdWRpbmcgY2FsbGVycywgaW1wb3J0ZXJzLCBkb2N1bWVudHMgaXQgY2hhbmdlcywgYW5kIHRlc3RzIHRoYXQgcGluIGEgY2hhbmdlZCBuYW1lLCB2YWx1ZSwgb3IgdmVyc2lvbi4gV2h5OiBhIGZvcmNlZCBmaWxlIG91dHNpZGUgdGhlIGZlbmNlIG1ha2VzIHRoZSB0aWNrZXQgaW1wb3NzaWJsZS4KLSBGcm9udG1hdHRlciBob2xkcyBvbmx5IGZpZWxkcyByZWFkIGJ5IHNjaGVkdWxpbmcsIGdhdGVzLCBvciBhdXRob3JpbmcvdHJpYWdlIHBvbGljeTsgYCMjIERlcGVuZHMgb25gIG5hbWVzIG9ubHkgbmVlZGVkIG1lcmdlZCBjb2RlOyBwdXQgYWxsIG90aGVyIG9yZGVyaW5nIGluIHByaW9yaXR5IG9yIGAjIyBSdW5zIGJlZm9yZWAsIG5ldmVyIGluIHByb3NlLgotIEhBUkQ6IFdoZW4gYSByZXBvcnRlZCBwcm9ibGVtIGhhcyBhIGNhdXNlIHRoYXQgd2lsbCByZWN1ciwgd3JpdGUgdHdvIHNlcGFyYXRlIHRpY2tldHMgaW4gdGhlIHNhbWUgdHVybi4gRmlyc3QgdGhlIGluc3RhbmNlIGZpeDogbWluaW1hbCBzY29wZSwgd3JpdHRlbiBiZWZvcmUgYW55IGNhdXNlIGRpYWdub3Npcy4gVGhlbiB0aGUgY2F1c2UgZml4LCBuZXZlciBmb2xkZWQgaW50byB0aGUgaW5zdGFuY2U7IHRoZSB0dXJuIGlzIHVuZmluaXNoZWQgdW50aWwgaXQgZXhpc3RzLiBCb3RoIGFyZSBzb2xpY2l0ZWQsIHNvIG5vIGFzayBpcyBuZWVkZWQuIFJvdXRpbmc6CiAgLSBQcm9kdWN0IGluc3RhbmNlOiBgcHJpb3JpdHk6IFAwYCwgbm8gYmxvY2tpbmcgZGVwZW5kcy4KICAtIFByb2R1Y3QgY2F1c2UgKGluZXJ0OyBkb2VzIG5vdCBzcHJlYWQgb24gaXRzIG93bik6IGBwcmlvcml0eTogUDFgLiBXaGVuIHRoZSB0d28gc2hhcmUgYW4gZWRpdCBzdXJmYWNlLCB0aGUgaW5zdGFuY2UgbGlzdHMgdGhlIGNhdXNlIGluIGAjIyBSdW5zIGJlZm9yZWAuCiAgLSBPcmNoZXN0cmF0aW9uIGNhdXNlIChzY2hlZHVsZXIsIGdhdGUsIGVudmlyb25tZW50LCBzaGFyZWQgbW9kdWxlLCBmaXh0dXJlIGZvcm1hdDsga2VlcHMgYnJlYWtpbmcgcnVucyB3aGlsZSBpdCBzaXRzKTogYHByaW9yaXR5OiBQMGAsIGAjIyBSdW5zIGJlZm9yZWAgZXZlcnkgdGlja2V0IGl0IHVuYmxvY2tzLCBuZXZlciBkZXBlbmRzIG9uIGEgcHJvZHVjdCBpbnN0YW5jZS4KLSBIQVJEOiBGb3IgdGlja2V0LXdvcnRoeSB3b3JrIHRoZSB1c2VyIGRpZCBub3QgYXNrIGZvciAoZm9sbG93LXVwLCBwcmV2ZW50aW9uLCBlbmZvcmNlbWVudCBsaW50LCBzd2VlcCksIHN0b3AgYmVmb3JlIGRpdmluZzogbmFtZSBpdCBpbiAxLTIgc2VudGVuY2VzIGFuZCBhc2sgdGhlIHVzZXIgdG8gY2hvb3NlIGF1dGhvciBub3csIGFmdGVyIHRoZSBjdXJyZW50IHRhc2ssIG9yIHNraXAuICJBZnRlciIgbWFrZXMgaXQgYW4gb3BlbiB0aHJlYWQuIEFubm91bmNlIGluIG9uZSBsaW5lIGFueSB1bnNvbGljaXRlZCBpbnZlc3RpZ2F0aW9uIGxvbmdlciB0aGFuIGEgY291cGxlIG9mIG1pbnV0ZXMuIFRoZSB1c2VyJ3MgcmVxdWVzdGVkIHRhc2sgYWx3YXlzIGdvZXMgZmlyc3QuIEF1dG9ub21vdXMgcnVucyBza2lwIHRoZSBhc2sgYW5kIGZpbGUgdG8gdGhlIFN1Z2dlc3Rpb24gQm94LgotIEZpbGUgYW4gdW5yZXF1ZXN0ZWQgaWRlYSBvciBzZWNvbmQgcHJvYmxlbSB3aXRoIGBjbHV0Y2ggYm94IHN1Z2dlc3QgIjxzdW1tYXJ5PiJgIGFuZCBuYW1lIGl0IGluIG9uZSBsaW5lLiBXaHk6IGEgbWFyZ2luIHN1Z2dlc3Rpb24gZGllcyB3aXRoIHRoZSBjaGF0LgotIEEgc3VwZXJ2aXNpbmcgc2Vzc2lvbiBtYXksIHVuYXNrZWQsIGZpeCBhIHRpY2tldCdzIGxpbnQgb3IgZm9ybWF0IGVycm9ycywgYWRkIGEgZmlsZSBtaXNzaW5nIGZyb20gYCMjIFNjb3BlIGZlbmNlYCBvciBgIyMgQ29udGV4dGAsIGNvcnJlY3QgYSBzdGFsZSBwYXRoLCBtYWtlIGEgc2ltcGxlIHdvcmRpbmcgdXBkYXRlLCBhbmQgcnVuIG9yIHJlc3RhcnQgdGhlIGRyYWluLiBJdCBtYXkgY29uZmlybSBvciByZWplY3QgYW5kIGVkaXQgYW55IHRpY2tldCBvbmx5IGFzIGEgYGNsdXRjaCBwcm9tcHQgZGlhZ25vc2VgIG9yIGBjbHV0Y2ggcHJvbXB0IGRyYWZ0c2AgUmVjb21tZW5kYXRpb24gbmFtZXMuIEl0IG1heSBub3QgcmV0cnkgYSBzdGVtIHdob3NlIGNhcHMgYXJlIHNwZW50IG9yIGVkaXQgYSBydW5uaW5nIHRpY2tldDsgY2hhbmdpbmcgYSB0aWNrZXQncyBnb2FsIG9yIHNjb3BlIHJlcXVpcmVzIHN1Y2ggYSBSZWNvbW1lbmRhdGlvbi4KCiMjIERpYWdub3NpcwoKLSBIQVJEOiBXaGVuIGEgcnVuIGZhaWxzLCBpcyBraWxsZWQsIHRpbWVzIG91dCwgc3RhbGxzLCBvciBlc2NhbGF0ZXMsIG5hbWUgaXRzIHJvb3QgY2F1c2UgaW4gb25lIHNlbnRlbmNlIGJlZm9yZSBlZGl0aW5nIHNwZWMgb3IgY29kZSBvciByZXJ1bm5pbmcuIFJlYWQgYGNsdXRjaCB2aWV3IHN0YXR1c2AsIGB0aWNrZXRzLzxzdGVtPi9gIChgcnVuLm1kYCwgYGNoZWNrcy5qc29uYCwgYGRpYWdub3Npcy5qc29uYCwgYHJldmlldy5tZGAsIGBhdHRlbXB0cy9gKSwgYW5kIHRoZSBlbmdpbmUgbG9nLiBGaXggdGhlIGNhdXNlIHdoZXJlIGl0IGxpdmVzLiBBbiBleHRlcm5hbCBjYXVzZSAoZW5naW5lLCBnYXRlLCBlbnZpcm9ubWVudCwgc2hhcmVkIG1vZHVsZSwgZml4dHVyZSwgZmxha3kgdGVzdCwgd3JvbmcgcHJlbWlzZSkgaXMgZml4ZWQgZmlyc3QgYW5kIG9yZGVyZWQgYWhlYWQgd2l0aCBwcmlvcml0eSBhbmQgYCMjIFJ1bnMgYmVmb3JlYC4gRG8gbm90IGFzc3VtZSB0aGUgdGlja2V0IGlzIHdyb25nLiBOZXZlciByZXJ1biBhIGZsYWt5IGZhaWx1cmUgdW50aWwgaXQgcGFzc2VzIGFuZCBjYWxsIHRoYXQgZml4ZWQuCi0gSEFSRDogV2hlbiBhIHN5bXB0b20gcmVjdXJzIG9uIGEgc3VyZmFjZSBhbHJlYWR5IGZpeGVkLCBuYW1lIHRoZSByb290IG1vZGVsIGFnYWluc3QgdGhlIGNhbm9uaWNhbCBzcGVjIChkZXNpZ24gZG9jcywgY29udHJhY3RzKSBhbmQgd3JpdGUgYSByb290LWNhdXNlIHRpY2tldCwgbm90IGFub3RoZXIgcGF0Y2guIEEgc2NvcGUgZmVuY2UgdGhhdCBmb3JiaWRzIHRvdWNoaW5nIHRoZSBzdXNwZWN0ZWQgcm9vdCBpcyBhIHJlZCBmbGFnOiByZS1zY29wZSBpdC4gVGVzdHMgdGhhdCBhc3NlcnQgdGhlIGN1cnJlbnQgd3JvbmcgYmVoYXZpb3IgcHJvdmUgbm90aGluZy4gTmV2ZXIgd3JpdGUgInRoZSBkZWZlY3Qgd2FzIG5vdCBYIiB3aXRob3V0IGNoZWNraW5nIHRoZSBzcGVjLgotIEhBUkQ6IFdpdGggZXZlcnkgZml4IG9yIGRpYWdub3NpcywgbmFtZSB0aGUgY2hhbmdlIHRoYXQgc3RvcHMgdGhlIHdob2xlIGNsYXNzIGZyb20gcmVjdXJyaW5nIChydWxlLCBsaW50LCBnYXRlLCB0ZW1wbGF0ZSBkZWZhdWx0LCBnZW5lcmF0b3IpIGFzIGEgc2VwYXJhdGUgaXRlbS4gQ2hlYXAgYW5kIGluIHNjb3BlOiBkbyBpdCB1bmRlciB0aGUgc2FtZSBhdXRob3JpemF0aW9uLiBDaGVhcCBidXQgb3V0IG9mIHNjb3BlOiBuYW1lIGl0LCB0aGVuIGZvbGxvdyB0aGUgYXNrIGZvciB1bnJlcXVlc3RlZCB3b3JrLiBFeHBlbnNpdmUgb3IgdW5jZXJ0YWluOiBgY2x1dGNoIGJveCBzdWdnZXN0YC4gU3RheWluZyBzaWxlbnQgaXMgdGhlIGZhaWx1cmUuCgotIEhBUkQ6IE91dHNpZGUgY2x1dGNoJ3Mgb3duIHJlcG8sIGEgZml4IHRoYXQgYmVsb25ncyBpbiBjbHV0Y2ggKGEgcHJvbXB0IHNwZWMsIGdhdGUsIHRpY2tldCBmb3JtYXQsIGhvc3QgZ3VpZGUsIG9yIHRoaXMgYmxvY2spIGlzIG5ldmVyIGNvcGllZCBvciBwYXRjaGVkIGludG8gaG9zdCBmaWxlcyBub3IgZmlsZWQgdG8gdGhlIFN1Z2dlc3Rpb24gQm94OyBuYW1lIGl0IHRvIHRoZSB1c2VyIGluIG9uZSBsaW5lLiBPbmx5IGEgYnVnIGluIGEgYGNsdXRjaCBib3ggaXNzdWVgIGNyaXRpY2FsIGNsYXNzIGdvZXMgdXBzdHJlYW06IGRyYWZ0IGEgYm9keSBmaWxlIChjbHV0Y2ggZmlsZSwgZGVmZWN0LCBtaW5pbWFsIGV2aWRlbmNlLCBubyBob3N0LXByaXZhdGUgY29kZSBvciBkYXRhKSwgYW5kIHdpdGggdGhlIHVzZXIncyBhZ3JlZW1lbnQgcnVuIGBjbHV0Y2ggYm94IGlzc3VlYCBhbmQgZ2l2ZSB0aGVtIHRoZSBsaW5rIHRvIHJldmlldyBhbmQgc3VibWl0OyB0aGVuIHN0b3AuIFdoeTogYSBob3N0IGNvcHkgY29tcGV0ZXMgd2l0aCBjbHV0Y2gncyBydWxlLCByZWFjaGVzIG5vIG90aGVyIGhvc3QsIGFuZCBnb2VzIHN0YWxlIG9uIHVwZ3JhZGUuCgojIyBDaGF0IHNlc3Npb24gY29uZHVjdAoKVGhlc2UgcnVsZXMgZ292ZXJuIGludGVyYWN0aXZlIGNoYXQgd2l0aCB0aGUgb3duZXIgcHJlc2VudC4gVGlja2V0IGFnZW50cyBza2lwIHRoaXMgc2VjdGlvbi4KCi0gSEFSRDogV2hlbiBhIHJlcGx5IHJhaXNlcyBtb3JlIHRoYW4gb25lIHF1ZXN0aW9uLCBvcHRpb24sIG9yIG5leHQgc3RlcCwgeW91IG93biB0aGF0IGxpc3Qgb2Ygb3BlbiB0aHJlYWRzLiBBY3Rpbmcgb24gb25lIG5ldmVyIGNsb3NlcyB0aGUgb3RoZXJzLiBFbmQgZWFjaCByZXBseSB3aXRoIGEgYFN0aWxsIG9wZW46YCBsaXN0IHVudGlsIHRoZSB1c2VyIHJlc29sdmVzIGVhY2ggb25lIG9yIHlvdSBjb21wbGV0ZSBpdCBhbmQgc2F5IHNvLiBJZiB1bnN1cmUsIGl0IGlzIG9wZW4uCi0gSEFSRDogTmV2ZXIgcnVuIG9yIG9mZmVyIGBnaXQgcHVzaGAsIGBnaCBwciBjcmVhdGVgLCBgZ2ggcHIgbWVyZ2VgLCBvciBhbnkgcmVtb3RlLW11dGF0aW5nIHZlcmIgdW5sZXNzIHRoZSB1c2VyIHNheXMgInB1c2giIHRoaXMgdHVybi4gQ29tbWl0IHdoZW4gYXNrZWQsIHRoZW4gc3RvcC4KLSBSZXNwZWN0IHRoZSBzaW5nbGUtd3JpdGVyIGxvY2tmaWxlOyB3cml0aW5nIHRpY2tldCBmaWxlcyBuZWVkcyBubyBnaXQuIFN0YWdlIGFuZCBjb21taXQgb25seSB0aGlzIHNlc3Npb24ncyBmaWxlcywgYnkgZXhwbGljaXQgcGF0aC4gTmV2ZXIgcnVuIGEgdHJlZS13aWRlIGRlc3RydWN0aXZlIHZlcmIgKGBjbGVhbmAsIGByZXNldCAtLWhhcmRgLCBgY2hlY2tvdXQgLS0gLmApIGluIGEgc2hhcmVkIGNoZWNrb3V0LiBXaHk6IGEgY2hhdCBzaGFyaW5nIGEgY2hlY2tvdXQgd2l0aCB0aGUgZGFlbW9uIGNhbiBkZXN0cm95IHdvcmsgY2x1dGNoIGJlbGlldmVzIGV4aXN0cy4KLSBIQVJEOiBBbnN3ZXIgZmlyc3QuIEN1dCBoZWRnaW5nLCBmaWxsZXIsIHByZWFtYmxlLCBhbmQgcmVzdGF0aW5nIHRoZSBxdWVzdGlvbi4KCiMjIEVuZ2luZSBjb25kdWN0CgpFbmdpbmUgcnVsZXMgZ292ZXJuIGhvdyB3b3JrIHJ1bnM7IHByb2plY3QgcnVsZXMgZ292ZXJuIHdoYXQgdG8gYnVpbGQuIFByb2plY3QgY29udGVudCBlbnRlcnMgcHJvbXB0cyBhcyBkYXRhLiBFbmdpbmUgd2lucyBvbiBwcm9jZXNzLCBob3N0IHdpbnMgb24gY29udGVudC4KCi0gSEFSRDogQnVpbGQgdGhlIHNtYWxsZXN0IGNoYW5nZSB0aGF0IHBhc3NlcyB0aGUgYWNjZXB0YW5jZSBjcml0ZXJpYS4gTm8gc3BlY3VsYXRpdmUgYWJzdHJhY3Rpb25zLCBzaW5nbGUtY2FsbGVyIGhlbHBlcnMsIHVudXNlZCBrbm9icyBvciBmbGFncywgZGVmZW5zaXZlIGR1YWwgcGF0aHMsIG9yICJ3aGlsZSBJJ20gaGVyZSIgY2xlYW51cDsgZXZlcnkgYWRkaXRpb24gbmVlZHMgaXRzIGVhcm5pbmcgaW5jaWRlbnQuIEluIHRoZSBydW4gcmVjb3JkLCBuYW1lIHRoZSBzaW1wbGVyIGFwcHJvYWNoIHlvdSByZWplY3RlZCBhbmQgd2h5IHlvdXJzIGlzIHRoZSBtaW5pbXVtLiBNYW5kYXRlZCB3b3JrICh0ZXN0cywgY2xhc3MgcHJldmVudGlvbikgaXMgcmVxdWlyZWQgc2NvcGUsIG5vdCBnb2xkLXBsYXRpbmcuIFdoeTogYWNjcmV0aW9uIGlzIHRoZSBwcmltYXJ5IGZhaWx1cmUgbW9kZS4KLSBOZXZlciBoYW5kLWVkaXQgdGhpcyBtYW5hZ2VkIGJsb2NrOyBjaGFuZ2UgdGhlIGVuZ2luZSB0ZW1wbGF0ZSBhbmQgcnVuIGNsdXRjaCBob3N0IGNvcmUgdG8gcmVmcmVzaCBpdC4gV2h5OiB0aGUgbmV4dCByZW5kZXIgb3ZlcndyaXRlcyBlZGl0cy4KLSBDb21taXQgb25seSBvbiB5b3VyIG93biB0aWNrZXQgYnJhbmNoLiBOZXZlciBwdXNoLCBvcGVuIHB1bGwgcmVxdWVzdHMsIG9yIHJ1biB0cmVlLXdpZGUgZGVzdHJ1Y3RpdmUgZ2l0OyB0aGUgZW5naW5lIG1lcmdlcyByZXZpZXdlZCB3b3JrIHRvIGxvY2FsIG1haW4uIFdoeTogbG9jYWwgbWFpbiBpcyB0aGUgYmxlc3NlZCBsaW5lLgotIEZpbGUgc2Vjb25kIHByb2JsZW1zIGluIHRoZSBTdWdnZXN0aW9uIEJveCwgbmV2ZXIgaW4gdGhpcyBkaWZmLiBWZXJpZnkgYSBwcmUtZXhpc3RpbmcgZmFpbHVyZSBvbiB0aGUgYmFzZSBjb21taXQgYmVmb3JlIGZpbGluZyBpdC4gV2h5OiBmb2xkZWQgZml4ZXMgaGlkZSBjYXVzZSBhbmQgZXhwYW5kIHNjb3BlLgotIFJlYWQgdGhlIG93bmluZyBhcnRpZmFjdCBiZWZvcmUgd3JpdGluZyBhIGNvbW1hbmQsIGNsYWltLCBvciB0ZXN0LiBXaHk6IGd1ZXNzZWQgZmFjdHMgY3JlYXRlIGNvc3RseSBidWdzLgo8IS0tIGNsdXRjaDpjb3JlIGVuZCAtLT4KCg=="


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
