import io
import mimetypes
import uuid
from typing import BinaryIO, TextIO, Union

_LINE_SEP = b'\r\n'


class MultiPartForm:
    """Accumulate the data to be used when posting a form."""

    def __init__(self, boundary=None):
        self._fields = []
        self._files = []
        self._boundary = boundary or uuid.uuid4().hex

    @property
    def method(self) -> str:
        return "POST"

    @property
    def content_type(self) -> str:
        return f'multipart/form-data; boundary={self._boundary}'

    def add_field(self,
                  field_name: str,
                  field_value: str):
        """Add a simple field to the form data."""
        self._fields.append((field_name, field_value))

    def add_file(self,
                 field_name: str,
                 file_name: str,
                 file_obj: Union[TextIO, BinaryIO, str],
                 mime_type: str = None):
        """Add a file to be uploaded."""
        if hasattr(file_obj, "read"):
            body = file_obj.read()
        else:
            with open(file_obj, "rb") as fp:
                body = fp.read()
        if isinstance(body, str):
            body = body.encode("utf-8")
        if mime_type is None:
            mime_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
        self._files.append((field_name, file_name, mime_type, body))

    def _boundary_line(self, final=False) -> bytes:
        line = f"--{self._boundary}"
        if final:
            line += "--"
        return line.encode('utf-8') + _LINE_SEP

    @staticmethod
    def _content_disposition_line(disposition_type="form-data", name: str = None, filename=None) -> bytes:
        line = f'Content-Disposition: {disposition_type}; name="{name}"'
        if filename:
            line += f'; filename="{filename}"'
        return line.encode('utf-8') + _LINE_SEP

    @staticmethod
    def _content_type_line(content_type: str) -> bytes:
        line = f'Content-Type: {content_type}'
        return line.encode('utf-8') + _LINE_SEP

    def __bytes__(self):
        """Return a byte-string representing the form data,
        including attached files.
        """
        buffer = io.BytesIO()

        # Add the form fields
        for field_name, field_value in self._fields:
            buffer.write(self._boundary_line())
            buffer.write(self._content_disposition_line(name=field_name))
            buffer.write(_LINE_SEP)
            buffer.write(field_value.encode('utf-8'))
            buffer.write(_LINE_SEP)

        for field_name, file_name, file_content_type, file_body in self._files:
            buffer.write(self._boundary_line())
            buffer.write(self._content_disposition_line(name=field_name, filename=file_name))
            buffer.write(self._content_type_line(content_type=file_content_type))
            buffer.write(_LINE_SEP)
            buffer.write(file_body if isinstance(file_body, bytes) else file_body.encode("utf-8"))
            buffer.write(_LINE_SEP)

        # Write final boundary
        buffer.write(self._boundary_line(final=True))
        return buffer.getvalue()

    def __str__(self):
        return bytes(self).decode("utf-8")
