---
id: declined-box-000467-215903ca
kind: declined
link: box-000467-215903ca
reopen_after_days: 30
---
A session says the chupa-* to clutch-* ticket-directory rename in commit b6512ac5 split eight stems from their journal history. The journal records all eight as merged under their chupa-* stems. The renamed clutch-* directories had no events, so a drain started 2026-11-15T11:27Z showed four of them as ready and re-ran work that was already merged. The other four showed as invalid. The session asks for the stems to be restored (restore-orphan-ticket-stems) and presents this as the cause behind box-000464.

There is nothing left to restore. No tickets/clutch-* or tickets/chupa-* directory exists on main now, because commit c09d48e0 removed the renamed directories. Records declined-box-000462-953131e6 and declined-box-000464-1f0626db both note this. With no committed ticket under any of the eight clutch-* stems, the drain has nothing to re-offer, so a restore ticket would do nothing that can be measured. The eight original chupa-* stems are still merged in the journal and need no repair. The real class is broader: renaming or re-adding a ticket directory for a stem that is already merged lets intake admit merged work again as a new stem. The incident shows this is possible, but it came from one deliberate bulk rename, and it is a different ticket from the one proposed. The related intake gap, where a staged rename drops the old stem without any check, was declined in declined-box-000091-41bb073d because there was no incident. Reopen if a clutch-* or chupa-* ticket directory reappears on main, or if another ticket-directory rename or copy makes the drain admit a stem whose work is already merged under another stem. At that point, author a cause ticket in which intake or lint refuses a new stem whose directory a staged rename made from a stem with journal history, and cite this incident and declined-box-000091-41bb073d.

- Glob tickets/clutch-*/** matches no files on main
- Glob tickets/{restore-orphan*,clutch-ruff*,clutch-test-gates,clutch-verdict*,chupa-*}/ticket.md matches no files
- All eight chupa-* stems (chupa-ruff-reclean, chupa-ruff-reclean-tests-a-l, chupa-ruff-reclean-tests-m-z, chupa-ruff-src, chupa-ruff-tests-a-k, chupa-ruff-tests-l-z, chupa-test-gates, chupa-verdict-multi-stem) are in the merged set
- None of the eight clutch-* stems is in the open-ticket list
- declined-box-000462-953131e6 and declined-box-000464-1f0626db both record that commit c09d48e0 removed the renamed ticket directories
- declined-box-000091-41bb073d already covers the rename-at-intake gap, where the old stem's deletion passes unchecked

Message: box-000467-215903ca
