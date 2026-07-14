# Repository E2E & Consistency Test Report
Date: Tue Jul 14 11:55:19 KST 2026

## SG_proj_001
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_001
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 3 items

tests/test_engine.py ...                                                 [100%]

============================== 3 passed in 1.33s ===============================
```
**Status: PASSED :white_check_mark:**

## SG_proj_002
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_002
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 17 items

tests/test_api.py ...                                                    [ 17%]
tests/test_diagnostics.py .                                              [ 23%]
tests/test_oblique_cases.py .                                            [ 29%]
tests/test_package_import.py ..                                          [ 41%]
tests/test_perspective.py ....                                           [ 64%]
tests/test_physics.py ......                                             [100%]

================================ tests coverage ================================
_______________ coverage: platform darwin, python 3.13.9-final-0 _______________

Name                             Stmts   Miss  Cover   Missing
--------------------------------------------------------------
deepdrop_sfe/__init__.py             5      0   100%
deepdrop_sfe/ai_engine.py          292    259    11%   19, 24-25, 28, 30, 34, 40, 43, 48-53, 63-75, 81-95, 102-130, 137-217, 224-275, 281-356, 362-460, 463
deepdrop_sfe/perspective.py         58      7    88%   32, 52-54, 59-60, 142
deepdrop_sfe/physics_engine.py     118     17    86%   59, 72, 82-83, 88, 149-153, 175-176, 186-189, 214
--------------------------------------------------------------
TOTAL                              473    283    40%
============================== 17 passed in 5.74s ==============================
```
**Status: PASSED :white_check_mark:**

## SG_proj_003
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_003
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 1 item

tests/test_import.py .                                                   [100%]

============================== 1 passed in 0.06s ===============================
```
**Status: PASSED :white_check_mark:**

## SG_proj_004
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_004
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 5 items

tests/test_main.py .....                                                 [100%]

============================== 5 passed in 0.85s ===============================
```
**Status: PASSED :white_check_mark:**

## SG_proj_005
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_005
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 7 items

tests/test_inference.py .....                                            [ 71%]
tests/test_train.py ..                                                   [100%]

============================== 7 passed in 1.17s ===============================
```
**Status: PASSED :white_check_mark:**

## SG_proj_006
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_006
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 3 items

tests/test_gpu_inference.py ...                                          [100%]

============================== 3 passed in 5.10s ===============================
```
**Status: PASSED :white_check_mark:**

## SG_proj_007
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_007
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 3 items

tests/test_api.py ..                                                     [ 66%]
tests/test_engine.py .                                                   [100%]

============================== 3 passed in 0.89s ===============================
```
**Status: PASSED :white_check_mark:**

## SG_proj_009
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_009
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 2 items

tests/test_ir_simulator.py ..                                            [100%]

=============================== warnings summary ===============================
../../../../../opt/homebrew/Caskroom/miniconda/base/lib/python3.13/site-packages/torch_geometric/llm/utils/backend_utils.py:26
  /opt/homebrew/Caskroom/miniconda/base/lib/python3.13/site-packages/torch_geometric/llm/utils/backend_utils.py:26: DeprecationWarning: `torch_geometric.distributed` has been deprecated since 2.7.0 and will no longer be maintained. For distributed training, refer to our tutorials on distributed training at https://pytorch-geometric.readthedocs.io/en/latest/tutorial/distributed.html or cuGraph examples at https://github.com/rapidsai/cugraph-gnn/tree/main/python/cugraph-pyg/cugraph_pyg/examples
    from torch_geometric.distributed import (

../../../../../opt/homebrew/Caskroom/miniconda/base/lib/python3.13/site-packages/requests/__init__.py:113
  /opt/homebrew/Caskroom/miniconda/base/lib/python3.13/site-packages/requests/__init__.py:113: RequestsDependencyWarning: urllib3 (2.5.0) or chardet (7.4.3)/charset_normalizer (3.4.4) doesn't match a supported version!
    warnings.warn(

tests/test_ir_simulator.py: 35 warnings
  /opt/homebrew/Caskroom/miniconda/base/lib/python3.13/site-packages/torch_geometric/inspector.py:433: DeprecationWarning: Failing to pass a value to the 'type_params' parameter of 'typing._eval_type' is deprecated, as it leads to incorrect behaviour when calling typing._eval_type on a stringified annotation that references a PEP 695 type parameter. It will be disallowed in Python 3.15.
    return typing._eval_type(value, _globals, None)  # type: ignore

tests/test_ir_simulator.py::test_optimize_mixture_ratios_backward_pass
  /Users/hyunchanan/Documents/GitHub/SG_proj_009/ir_simulator.py:832: UserWarning: 'data.DataLoader' is deprecated, use 'loader.DataLoader' instead
    loader = DataLoader(data_list, batch_size=len(data_list), shuffle=False)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 2 passed, 38 warnings in 6.00s ========================
```
**Status: PASSED :white_check_mark:**

## SG_proj_010
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_010
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 2 items

tests/test_main.py ..                                                    [100%]

=============================== warnings summary ===============================
tests/test_main.py::test_detect_surface_sus
tests/test_main.py::test_detect_surface_unknown
  /opt/homebrew/Caskroom/miniconda/base/lib/python3.13/site-packages/sklearn/utils/validation.py:2691: UserWarning: X does not have valid feature names, but MinMaxScaler was fitted with feature names
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 2 passed, 2 warnings in 1.06s =========================
```
**Status: PASSED :white_check_mark:**

## SG_proj_011
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_011
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 5 items

tests/test_main.py ..                                                    [ 40%]
tests/test_model.py ...                                                  [100%]

================================ tests coverage ================================
_______________ coverage: platform darwin, python 3.13.9-final-0 _______________

Name              Stmts   Miss  Cover   Missing
-----------------------------------------------
src/__init__.py       0      0   100%
src/main.py          10      0   100%
src/model.py         40     13    68%   15, 34-35, 39-47, 56, 58
src/schemas.py        9      0   100%
-----------------------------------------------
TOTAL                59     13    78%
============================== 5 passed in 0.27s ===============================
```
**Status: PASSED :white_check_mark:**

## SG_proj_012
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_012
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 2 items

tests/test_main.py ..                                                    [100%]

============================== 2 passed in 0.21s ===============================
```
**Status: PASSED :white_check_mark:**

## SG_proj_013
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_013
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 3 items

tests/test_main.py ...                                                   [100%]

============================== 3 passed in 0.18s ===============================
```
**Status: PASSED :white_check_mark:**

## SG_proj_014
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_014
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 2 items

tests/test_main.py ..                                                    [100%]

=============================== warnings summary ===============================
tests/test_main.py::test_orchestrate_matched[asyncio]
  /Users/hyunchanan/Documents/GitHub/SG_proj_014/src/orchestrator.py:336: PydanticDeprecatedSince20: The `dict` method is deprecated; use `model_dump` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    "processability": proc_result.dict()

tests/test_main.py::test_orchestrate_reverse_engineered[asyncio]
  /Users/hyunchanan/Documents/GitHub/SG_proj_014/src/orchestrator.py:328: PydanticDeprecatedSince20: The `dict` method is deprecated; use `model_dump` instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.12/migration/
    "processability": proc_result.dict()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 2 passed, 2 warnings in 0.37s =========================
```
**Status: PASSED :white_check_mark:**

## SG_proj_015
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_proj_015
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 0 items

============================ no tests ran in 1.17s =============================
```
**Status: PASSED :white_check_mark:**

## SG_integration_step1
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_integration_step1
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 5 items

tests/test_imports.py ..                                                 [ 40%]
tests/test_integration.py ...                                            [100%]

============================== 5 passed in 4.31s ===============================
```
**Status: PASSED :white_check_mark:**

## SG_integration_step2
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_integration_step2
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 1 item

tests/test_dummy.py .                                                    [100%]

============================== 1 passed in 0.06s ===============================
```
**Status: PASSED :white_check_mark:**

## SG_integration_step3
```text
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.0.3, pluggy-1.5.0
rootdir: /Users/hyunchanan/Documents/GitHub/SG_integration_step3
configfile: pyproject.toml
plugins: anyio-4.12.1, cov-7.1.0, hypothesis-6.155.7, hydra-core-1.3.2, respx-0.23.1
collected 1 item

tests/test_dummy.py .                                                    [100%]

============================== 1 passed in 0.06s ===============================
```
**Status: PASSED :white_check_mark:**

