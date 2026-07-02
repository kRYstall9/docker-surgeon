# [2.1.0](https://github.com/kRYstall9/docker-surgeon/compare/v2.0.0...v2.1.0) (2026-07-02)


### Features

* add agent placeholder for notifications ([87a11ee](https://github.com/kRYstall9/docker-surgeon/commit/87a11eef758ebad58d1f32456e38d8944fb0df91))

# [2.0.0](https://github.com/kRYstall9/docker-surgeon/compare/v1.5.0...v2.0.0) (2026-06-13)


* refactor(core)!: introduce Runtime and isolate server/agent execution ([516d473](https://github.com/kRYstall9/docker-surgeon/commit/516d473d6925ae2efe455f1ff7db85f991564913)), closes [#12](https://github.com/kRYstall9/docker-surgeon/issues/12)


### BREAKING CHANGES

* server, agent and dashboard must run same version due to runtime coupling.

# [1.5.0](https://github.com/kRYstall9/docker-surgeon/compare/v1.4.2...v1.5.0) (2026-04-14)


### Features

* add multi-host support via agents ([#5](https://github.com/kRYstall9/docker-surgeon/issues/5)) ([3be3216](https://github.com/kRYstall9/docker-surgeon/commit/3be3216841be556e8d7eae51d236909bb8c14c0e))

## [1.4.2](https://github.com/kRYstall9/docker-surgeon/compare/v1.4.1...v1.4.2) (2025-11-19)


### Bug Fixes

* the JSON object must be str, bytes or bytearray, not list ([13cc185](https://github.com/kRYstall9/docker-surgeon/commit/13cc1852c59c3fb09421c95a2c66af16b8b8b2e8))

## [1.4.1](https://github.com/kRYstall9/docker-surgeon/compare/v1.4.0...v1.4.1) (2025-11-19)


### Bug Fixes

* 'bool' object has no attribute 'lower' ([9e28c85](https://github.com/kRYstall9/docker-surgeon/commit/9e28c850c0dba8a02d23fb43fc97a754c59fadd5))

# [1.4.0](https://github.com/kRYstall9/docker-surgeon/compare/v1.3.0...v1.4.0) (2025-11-18)


### Features

* add real-time notification support using Apprise ([dfec9d4](https://github.com/kRYstall9/docker-surgeon/commit/dfec9d4411cf81acc6224e9b637484cd2d2cef94)), closes [#1](https://github.com/kRYstall9/docker-surgeon/issues/1)

# [1.3.0](https://github.com/kRYstall9/docker-surgeon/compare/v1.2.0...v1.3.0) (2025-11-17)


### Features

* add dashboard ([4dd4428](https://github.com/kRYstall9/docker-surgeon/commit/4dd442841483b9567e8907706fb71678932c002e))

# [1.2.0](https://github.com/kRYstall9/docker-surgeon/compare/v1.1.1...v1.2.0) (2025-11-16)


### Features

* improve event handling, logging and error robustness ([b00112f](https://github.com/kRYstall9/docker-surgeon/commit/b00112f651c92a6f12026b488a2f2c82ee84d2d9))
