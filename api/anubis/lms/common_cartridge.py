import io
import posixpath
import zipfile
import zlib
from urllib.parse import urlparse
from xml.etree import ElementTree


MAX_PACKAGE_SIZE = 25 * 1024 * 1024
MAX_EXPANDED_SIZE = 256 * 1024 * 1024
MAX_PACKAGE_ENTRIES = 4096
MAX_DESCRIPTOR_SIZE = 2 * 1024 * 1024


def _local_name(element):
    return element.tag.rsplit("}", 1)[-1]


def _relative_path(base, href):
    if not href or "\\" in href or href.startswith("/"):
        raise ValueError("Invalid file path in Common Cartridge manifest.")
    parsed = urlparse(href)
    path = posixpath.normpath(posixpath.join(posixpath.dirname(base), href))
    if parsed.scheme or parsed.netloc or path in {".", ".."} or path.startswith("../"):
        raise ValueError("Invalid file path in Common Cartridge manifest.")
    return path


def _read_xml(archive, name, max_size):
    try:
        info = archive.getinfo(name)
        if info.file_size > max_size or info.flag_bits & 1:
            raise ValueError("Common Cartridge XML file is too large or encrypted.")
        content = archive.read(info)
    except (KeyError, RuntimeError, NotImplementedError, OSError, zipfile.BadZipFile, zlib.error) as error:
        raise ValueError("Common Cartridge references an unreadable XML file.") from error
    normalized = content.upper().replace(b"\x00", b"")
    if b"<!DOCTYPE" in normalized or b"<!ENTITY" in normalized:
        raise ValueError("Common Cartridge XML cannot contain document type declarations.")
    try:
        return ElementTree.fromstring(content)
    except ElementTree.ParseError as error:
        raise ValueError("Common Cartridge contains invalid XML.") from error


def extract_web_links(package):
    """Return Common Cartridge IMS Web Links and the number of skipped resources."""
    if not package or len(package) > MAX_PACKAGE_SIZE:
        raise ValueError("Common Cartridge must be smaller than 25 MiB.")

    try:
        archive = zipfile.ZipFile(io.BytesIO(package))
    except (OSError, zipfile.BadZipFile) as error:
        raise ValueError("Upload a valid Common Cartridge .imscc file.") from error

    with archive:
        try:
            entries = archive.infolist()
        except (OSError, zipfile.BadZipFile) as error:
            raise ValueError("Upload a valid Common Cartridge .imscc file.") from error
        if len(entries) > MAX_PACKAGE_ENTRIES or sum(item.file_size for item in entries) > MAX_EXPANDED_SIZE:
            raise ValueError("Common Cartridge contains too many or too-large files.")
        if len({item.filename for item in entries}) != len(entries):
            raise ValueError("Common Cartridge contains duplicate file paths.")

        manifests = [item.filename for item in entries if item.filename.casefold() == "imsmanifest.xml"]
        if len(manifests) != 1:
            raise ValueError("Common Cartridge must contain one imsmanifest.xml at its root.")
        manifest_name = manifests[0]
        manifest = _read_xml(archive, manifest_name, MAX_DESCRIPTOR_SIZE)

        titles = {}
        for item in manifest.iter():
            if _local_name(item) == "item" and item.get("identifierref"):
                title = next(
                    (child.text.strip() for child in item if _local_name(child) == "title" and child.text),
                    "",
                )
                if title:
                    titles.setdefault(item.get("identifierref"), title)

        links = []
        skipped = 0
        for resource in manifest.iter():
            if _local_name(resource) != "resource":
                continue
            if resource.get("type", "").casefold() not in {
                "imswl_xmlv1p0", "imswl_xmlv1p1", "imswl_xmlv1p2", "imswl_xmlv1p3", "imswl_xmlv1p4",
            }:
                skipped += 1
                continue

            descriptor_xml = next(
                (child for child in resource if _local_name(child) == "webLink"),
                None,
            )
            if descriptor_xml is None:
                descriptor = next(
                    (child.get("href") for child in resource
                     if _local_name(child) == "file" and child.get("href")),
                    None,
                )
                descriptor_name = _relative_path(manifest_name, descriptor)
                descriptor_xml = _read_xml(archive, descriptor_name, MAX_DESCRIPTOR_SIZE)
            url = next(
                (element.get("href") for element in descriptor_xml.iter() if _local_name(element) == "url"),
                None,
            )
            parsed = urlparse(url or "")
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("Common Cartridge contains a web link that is not a safe HTTP or HTTPS URL.")

            descriptor_title = next(
                (element.text.strip() for element in descriptor_xml.iter()
                 if _local_name(element) == "title" and element.text and element.text.strip()),
                "",
            )
            title = titles.get(resource.get("identifier")) or descriptor_title or parsed.hostname
            links.append((title[:16384], url))

        if not links:
            raise ValueError("This cartridge has no supported IMS Web Link resources.")
        # ponytail: This maps IMS Web Links only; add QTI and local pages when Anubis can represent them.
        return links, skipped
