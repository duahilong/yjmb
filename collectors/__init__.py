# collectors 包 - 硬件采集模块
# 导入所有 collector 模块以触发 @register_collector 装饰器注册

def load_all():
    """导入所有采集模块，触发注册"""
    from collectors import os_info      # noqa: F401
    from collectors import motherboard  # noqa: F401
    from collectors import cpu          # noqa: F401
    from collectors import memory       # noqa: F401
    from collectors import gpu          # noqa: F401
    from collectors import storage      # noqa: F401
    from collectors import network      # noqa: F401
    from collectors import audio        # noqa: F401
    from collectors import monitor      # noqa: F401
