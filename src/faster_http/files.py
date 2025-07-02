"""File upload utilities for faster-http."""
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union


class FileUpload:
    """文件上传类 - 与 httpx files 参数对齐"""
    
    def __init__(self, content=None, filename=None, content_type=None):
        self.content = content
        self.filename = filename
        self.content_type = content_type
    
    def to_bytes(self):
        """Convert content to bytes for compatibility."""
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, str):
            # 如果是文件路径，读取文件
            try:
                path = Path(self.content)
                if path.exists():
                    with open(path, 'rb') as f:
                        return f.read()
                else:
                    # 当作字符串内容
                    return self.content.encode('utf-8')
            except Exception:
                # 当作字符串内容
                return self.content.encode('utf-8')
        elif hasattr(self.content, 'read'):
            # 文件对象
            return self.content.read()
        else:
            return str(self.content).encode('utf-8')
    
    def get_content_type(self):
        """Get content type for the file."""
        if self.content_type:
            return self.content_type
        
        # 如果有文件名，尝试从扩展名猜测
        if self.filename:
            content_type, _ = mimetypes.guess_type(self.filename)
            if content_type:
                return content_type
        
        # 根据内容类型猜测
        if isinstance(self.content, str):
            if self.content.strip().startswith(('<', '{')):
                return 'text/plain'
            return 'text/plain'
        
        # 默认为二进制流
        return 'application/octet-stream'


def _process_single_file(file_spec: Any) -> FileUpload:
    """处理单个文件规格 - 与 httpx 对齐"""
    if isinstance(file_spec, FileUpload):
        return file_spec
    
    elif isinstance(file_spec, bytes):
        return FileUpload(content=file_spec)
    
    elif isinstance(file_spec, (str, Path)):
        # 简单检查：如果是路径则作为文件，否则作为内容
        if Path(file_spec).exists():
            return FileUpload(content=file_spec, filename=Path(file_spec).name)
        else:
            return FileUpload(content=file_spec.encode('utf-8'))
    
    elif hasattr(file_spec, 'read'):
        # 文件对象
        filename = getattr(file_spec, 'name', None)
        if filename:
            filename = os.path.basename(filename)
        return FileUpload(content=file_spec, filename=filename)
    
    elif isinstance(file_spec, (tuple, list)) and len(file_spec) >= 2:
        # httpx 格式: (filename, content) 或 (filename, content, content_type)
        filename = file_spec[0]
        content = file_spec[1]
        content_type = file_spec[2] if len(file_spec) > 2 else None
        return FileUpload(content=content, filename=filename, content_type=content_type)
    
    else:
        # 其他情况当作内容处理
        return FileUpload(content=file_spec)


def process_files_parameter(files: Optional[Dict[str, Any]]) -> Optional[Dict[str, FileUpload]]:
    """处理 files 参数 - 与 httpx 对齐"""
    if not files:
        return None
    
    return {field_name: _process_single_file(file_spec) 
            for field_name, file_spec in files.items()}


def _process_string_or_path(file_spec: Union[str, Path]) -> FileUpload:
    return _process_single_file(file_spec)


def _process_file_like_object(file_spec) -> FileUpload:
    return _process_single_file(file_spec)


def _process_tuple_format(file_spec) -> FileUpload:
    return _process_single_file(file_spec) 