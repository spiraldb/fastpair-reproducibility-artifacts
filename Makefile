.PHONY: verify
# Reproduce the paper's data artifacts: rebuild every figure from committed results/
# and re-derive every headline number. Requires `uv` (https://docs.astral.sh/uv/).
verify:
	bash experiments/verify.sh
