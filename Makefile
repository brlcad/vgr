.PHONY: all simh media test shell calibrate benchmark benchmark-calibrated metrics metrics-calibrated

all: simh media

simh:
	./scripts/build-simh.sh

media:
	./scripts/fetch-sources.sh

test:
	python3 -m unittest discover -s tests -v

shell:
	./scripts/run-vax.sh shell

calibrate:
	./scripts/run-vax.sh calibrate

benchmark:
	./scripts/run-vax.sh benchmark

benchmark-calibrated:
	VGR_THROTTLE=462K ./scripts/run-vax.sh benchmark

metrics:
	@latest=$$(ls -t results/*.console.log | head -1); \
	args=; \
	if test -n "$$VGR_THROTTLE"; then args="--throttle $$VGR_THROTTLE"; fi; \
	python3 tools/vgr_metrics.py --capture "$$latest" $$args

metrics-calibrated:
	@latest=$$(ls -t results/*.console.log | head -1); \
	python3 tools/vgr_metrics.py --capture "$$latest" --throttle 462K
