# Fairino Collision Issue
## Software 3.8.4.2
When a collision happens, the arm has heavy vibration during subsequent movement. The only "fix" I have found is to not move the arm for many seconds and then future arm movements will not vibrate.

Run the `main.py` script here to replicate the issue. When the arm is moving slowly, apply extra torque to J5. This will trigger a collision which is cleared. Then as the arm moves up and down, rest your hand on top of the end flange. You will feel the extra vibrations in movement. They might not happen right away, it can take a few iterations and they are not consistent. Somtimes, the vibrations will be so extreme it will cause a collision error even on the highest collision threshold.

```
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

uv sync
uv run main.py
```
