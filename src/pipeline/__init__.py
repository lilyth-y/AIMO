"""
Pipeline 모듈 초기화 파일
"""

# Lazy imports to avoid loading heavy dependencies unless needed
def __getattr__(name):
    if name == "PipelineOrchestrator":
        from .orchestrator import PipelineOrchestrator
        return PipelineOrchestrator
    elif name == "settings":
        from .settings import settings
        return settings
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'PipelineOrchestrator',
    'settings',
]
