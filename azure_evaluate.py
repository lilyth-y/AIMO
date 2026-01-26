import os
import json
from azure.ai.evaluation import evaluate, TaskAdherenceEvaluator, ToolCallAccuracyEvaluator

# (예시) OpenAI 모델 설정 - 실제 환경에 맞게 수정 필요
# from azure.ai.evaluation import OpenAIModelConfiguration
# model_config = OpenAIModelConfiguration(
#     type="openai",
#     model="gpt-4",
#     base_url="https://api.openai.com/v1",
#     api_key=os.environ.get("OPENAI_API_KEY")
# )

# (예시) Azure OpenAI 모델 설정 - 실제 환경에 맞게 수정 필요
from azure.ai.evaluation import AzureOpenAIModelConfiguration
model_config = AzureOpenAIModelConfiguration(
    azure_deployment="<YOUR_DEPLOYMENT_NAME>",
    azure_endpoint="<YOUR_AZURE_OPENAI_ENDPOINT>",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version="2025-04-01-preview"
)

# Custom code-based evaluator: 코드 실행 성공 여부 평가
class CodeExecutionSuccessEvaluator:
    def __init__(self):
        pass
    def __call__(self, *, result: dict, **kwargs):
        # result: {'output': ..., 'error': ..., ...}
        if result and result.get('error') is None:
            return {"code_execution_success": 1}
        return {"code_execution_success": 0}

# 평가기 생성
adherence_eval = TaskAdherenceEvaluator(model_config=model_config)
tool_eval = ToolCallAccuracyEvaluator(model_config=model_config)
code_eval = CodeExecutionSuccessEvaluator()

data_path = "eval_data.jsonl"
output_path = "eval_results.jsonl"

result = evaluate(
    data=data_path,
    evaluators={
        "task_adherence": adherence_eval,
        "tool_usage_accuracy": tool_eval,
        "code_execution_success": code_eval
    },
    evaluator_config={
        "task_adherence": {
            "column_mapping": {
                "query": "${data.query}",
                "response": "${data.response}"
            }
        },
        "tool_usage_accuracy": {
            "column_mapping": {
                "query": "${data.query}",
                "response": "${data.response}",
                "tool_definitions": "${data.tools}"
            }
        },
        "code_execution_success": {
            "column_mapping": {
                "result": "${data.result}"
            }
        }
    },
    output_path=output_path
)

print(f"✅ 평가 완료. 결과: {output_path}")
