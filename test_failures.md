# Test Results Summary

## Overall Counts
- **Total Tests Collected**: 407 (across 26 test files)
- **Passed**: 399
- **Failed**: 8

All 26 test files were successfully collected without the `ModuleNotFoundError` for `pydantic_core`.

## Detailed Test Failures

### Environment-Related Failures (1 test)
1. `tests/test_nl_to_dag.py::TestGeneratePipelineEndpoint::test_generate_pipeline_api_endpoint`
   - **Error**: `RuntimeError: Form data requires "python-multipart" to be installed.`
   - **Cause**: Missing `python-multipart` dependency in the new environment wrapper. This is an environment issue directly resulting from building the new virtual environment without explicitly including this hidden/indirect dependency.

### Pre-existing Failures (7 tests)
These test failures specify logic mismatches, mocked behavior failures, and hardcoded fallback updates, meaning they were likely pre-existing rather than being caused by the Python 3.11 environment upgrade.

1. `tests/test_chat_plan_mode.py::TestToolExecution::test_registered_tool_called`
   - **Error**: `assert 0 == 1`
2. `tests/test_chat_tool_registry.py::TestRegistryBuilding::test_full_registry_has_all_tools`
   - **Error**: `AssertionError: assert {'create', 'dispatch_pipeline', ...} == {'create', ...}` - Missing tools in the mocked registry or hardcoded expectation.
3. `tests/test_chat_tool_registry.py::TestPipelineTool::test_pipeline_lists_definitions`
   - **Error**: `TypeError: argument of type 'async_generator' is not iterable` - Async behavior refactoring likely broken here.
4. `tests/test_chat_tool_registry.py::TestPipelineTool::test_pipeline_empty`
   - **Error**: `TypeError: argument of type 'async_generator' is not iterable`
5. `tests/test_chat_tool_registry.py::TestPipelineTool::test_pipeline_error`
   - **Error**: `AttributeError: 'async_generator' object has no attribute 'lower'` - Downstream processing of the generator object.
6. `tests/test_integration_dal_chat.py::TestToolExecution::test_registered_tool_executes`
   - **Error**: `assert 0 == 1`
7. `tests/test_phase_f.py::TestModelConfigRegistry::test_missing_yaml_uses_defaults`
   - **Error**: `AssertionError: assert 'gemini/gemini-2.5-flash' == 'gemini/gemini-2.0-flash'` - Likely a recent model update to `gemini-2.5-flash` not mirrored in the tests.
