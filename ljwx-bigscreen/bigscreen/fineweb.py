from datatrove.executor import LocalPipelineExecutor
from datatrove.pipeline.readers import ParquetReader
from datatrove.pipeline.filters import LambdaFilter
from datatrove.pipeline.writers import JsonlWriter

pipeline_exec = LocalPipelineExecutor(
    pipeline=[
        ParquetReader("hf://datasets/HuggingFaceFW/fineweb/data/CC-MAIN-2024-10", limit=1000),
        LambdaFilter(lambda doc: "hugging" in doc.text),
        JsonlWriter("some-output-path")
    ],
    tasks=10
)
pipeline_exec.run()