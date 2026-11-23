---
id: declined-box-001107-050baa61
kind: declined
link: box-001107-050baa61
reopen_after_days: 30
---
Proposes a guard against config-model methods being called from stage or runner code. Under serve and drain those stages get a field-only ConfigSnapshot, so any such method call raises AttributeError, while unit tests pass because they use a real Config. The trigger was TrainingData.effective_exclude, which failed silently inside harvest until commit 4ecf3a4e replaced it with the plain function training_exclude.

The single incident is already fixed. clutch/config.py now has training_exclude as a plain function, and its docstring names the ConfigSnapshot hazard. The only method left on a config model is TrainingData.require_enabled, and its one caller is clutch/__main__.py:1973, a CLI path that holds a real Config, not a ConfigSnapshot. No stage-reachable config method exists today, so there is no reachable wrong runtime behavior. The proposed guard is a prevention test only. Reopen if a stage-, runner- or serve-reachable path calls a method or property on a config model, or if another AttributeError from a ConfigSnapshot shows up in a serve or drain run.

- clutch/config.py:373-397: ConfigSnapshot exposes only fields through __getattr__, and snapshot_config freezes model fields only
- clutch/config.py:300: TrainingData.require_enabled is the only remaining method on a config model
- clutch/__main__.py:1973: require_enabled has one caller, a CLI path with a real Config
- clutch/config.py:308-309: training_exclude is now a plain function whose docstring cites the ConfigSnapshot hazard (fix 4ecf3a4e)

Message: box-001107-050baa61
