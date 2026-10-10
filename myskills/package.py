"""Export precisely the hashed file set. Never execute a source checkout directly."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from .digest import canonical_bytes, package_files, verify_package
from .manifest import validate_manifest

def export_package(root, manifest):
    validate_manifest(manifest)
    verify_package(root, manifest)
    output = BytesIO()
    with ZipFile(output, 'w', compression=ZIP_DEFLATED) as archive:
        archive.writestr(ZipInfo('manifest.json'), canonical_bytes(manifest))
        for record in package_files(root):
            info = ZipInfo('skill/' + record['path'])
            info.external_attr = (0o100755 if record['executable'] else 0o100644) << 16
            archive.writestr(info, (Path(root) / record['path']).read_bytes())
    # Reject changes during collection. This is an offline build, not custody fencing.
    verify_package(root, manifest)
    return output.getvalue()
