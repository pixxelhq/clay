# Changelog

## v0.6.0 - 18-09-2024
### New Features
- Input assets will also be pushed to s3 for job runner v2
### Fixes
- Minor refactor of job runner v2

## v0.5.0 - 11-09-2024
### New Features
- Added support for `group` to data spec by @pranjaldatta. [(043af0d)](https://github.com/example/clay/commit/043af0d7b7d2ef6067fa0fbbe7effb4c7a6b7016)
### Fixes
- Input vector files now get uploaded to S3 for both inferences and workflows by @sanafirdaus. [(eb435f0)](https://github.com/example/clay/commit/eb435f0082ae8be1e261b5b1c743484f082f2b3f)

## v0.4.11 - 14-08-2024
### New Features
- Orchestrator Callback URL is now configurable and injected at runtime via orchestrator by @pranjaldatta. [(4107ed6)](https://github.com/example/clay/commit/4107ed6e546772a5bf14ecabe8b04bbb70d994e5)

## v0.4.10 - 23-07-2024
### New Features
- Support for stac urls in `RasterProperties` by @pranjaldatta. [(4f0031e)](https://github.com/example/clay/commit/4f0031e229c5d516a9e79c080eac6a13b9862761)

## v0.4.6 - 28-06-2024
### New Features
- Added `date` to `RasterProperties` by @sanafirdaus. [(6e50abd)](https://github.com/example/clay/commit/6e50abd875d95b5e886af307a1e8f26cd44ec078)
- Added time metrics to inference callback by @pranjaldatta. [(c3c192b)](https://github.com/example/clay/commit/c3c192b16f3863453c0580bf8b83c767143f97b0)
### Fixes
- Improved time calculation for total model runtime and inference runtime by @pranjaldatta. [(d2c751)](https://github.com/example/clay/commit/d2c751086cc6fe8deea73f266804a315bf3ed9f0)
