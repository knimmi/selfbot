@nightyScript(
    name="EZ-Bio File Upload 2",
    author="windowsed",
    description="Upload files and images to e-z.gg file hosting service",
    usage="<p>ezupload [url] | <p>ezupload key <api_key>"
)
def ez_upload_script():
    """
    EZ-BIO FILE UPLOAD
    ------------------
    Upload files and images to e-z.gg hosting (100MB limit).

    COMMANDS:
    <p>ezupload - Upload an attached file
    <p>ezupload <url> - Download a URL and upload it
    <p>ezupload key <api_key> - Save your e-z.gg API key
    <p>ezupload help - Show usage

    EXAMPLES:
    <p>ezupload  (attach a file)
    <p>ezupload https://example.com/image.png
    <p>ezupload key ez_xxxxxxxx

    NOTES:
    - Requires `aiohttp` (bundled with Nighty)
    - Maximum file size: 100MB
    - Supports video, image, audio, and common application files
    - Success embed includes view, raw, and deletion URLs
    """
    import asyncio
    import json
    from datetime import datetime
    from urllib.parse import unquote, urlparse

    import aiohttp

    SCRIPT_NAME = "EZ-Bio File Upload"
    CONFIG_KEY = "ezupload_api_key"
    API_URL = "https://api.e-z.gg/files"
    MAX_SIZE = 100 * 1024 * 1024
    USER_AGENT = "Nighty-EZUpload/1.0"
    CHUNK = 64 * 1024

    MIME_BY_EXT = {
        "mp4": "video/mp4",
        "avi": "video/x-msvideo",
        "mov": "video/quicktime",
        "wmv": "video/x-ms-wmv",
        "flv": "video/x-flv",
        "webm": "video/webm",
        "mkv": "video/x-matroska",
        "3gp": "video/3gpp",
        "ogv": "video/ogg",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        "ico": "image/x-icon",
        "tiff": "image/tiff",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "flac": "audio/flac",
        "aac": "audio/aac",
        "ogg": "audio/ogg",
        "wma": "audio/x-ms-wma",
        "m4a": "audio/mp4",
        "opus": "audio/opus",
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "txt": "text/plain",
        "rtf": "application/rtf",
        "zip": "application/zip",
        "rar": "application/vnd.rar",
        "7z": "application/x-7z-compressed",
        "tar": "application/x-tar",
        "gz": "application/gzip",
        "json": "application/json",
        "xml": "application/xml",
        "csv": "text/csv",
    }
    IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "ico", "tiff"}
    TYPE_EMOJI = {
        "video": "🎥",
        "image": "🖼️",
        "audio": "🎵",
        "application": "📄",
        "text": "📝",
    }

    def script_log(message: str, level: str = "INFO"):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] [{SCRIPT_NAME}] [{level}] {message}", type_=level)

    def file_ext(filename: str) -> str:
        name = (filename or "").rsplit(".", 1)
        return name[-1].lower() if len(name) == 2 else ""

    def content_type_for(filename: str, fallback: str = ""):
        ext = file_ext(filename)
        if ext in MIME_BY_EXT:
            return MIME_BY_EXT[ext]
        if fallback:
            mime = fallback.split(";", 1)[0].strip().lower()
            major = mime.split("/", 1)[0] if "/" in mime else ""
            if major in ("video", "image", "audio", "application", "text"):
                return mime
        return None

    def filename_from_url(url: str) -> str:
        path = unquote(urlparse(url).path)
        name = path.rsplit("/", 1)[-1].strip()
        return name or "uploaded_file"

    def result_url(result: dict, *keys: str) -> str:
        for key in keys:
            value = result.get(key)
            if value:
                return str(value)
        return ""

    async def send_temp(ctx, text: str):
        msg = await ctx.send(text, silent=True)
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass

    async def send_embed(channel_id, title: str, content: str, image=None):
        prev_private = getConfigData().get("private")
        updateConfigData("private", False)
        try:
            await forwardEmbedMethod(
                channel_id=channel_id,
                title=title,
                content=content,
                image=image,
            )
        finally:
            updateConfigData("private", prev_private)

    async def download_url(session: aiohttp.ClientSession, url: str):
        timeout = aiohttp.ClientTimeout(total=120)
        async with session.get(url, timeout=timeout, allow_redirects=True) as resp:
            if resp.status != 200:
                body = (await resp.text())[:200]
                raise RuntimeError(f"download failed ({resp.status}): {body}")

            declared = resp.headers.get("Content-Length")
            if declared and int(declared) > MAX_SIZE:
                raise ValueError("too_large")

            chunks = []
            size = 0
            async for chunk in resp.content.iter_chunked(CHUNK):
                size += len(chunk)
                if size > MAX_SIZE:
                    raise ValueError("too_large")
                chunks.append(chunk)

            name = filename_from_url(str(resp.url)) or filename_from_url(url)
            header_type = resp.headers.get("Content-Type", "")
            return b"".join(chunks), name, header_type

    async def upload_file(session: aiohttp.ClientSession, api_key: str, filename: str, file_data: bytes, content_type: str):
        form = aiohttp.FormData()
        form.add_field("file", file_data, filename=filename, content_type=content_type)
        timeout = aiohttp.ClientTimeout(total=180)
        async with session.post(
            API_URL,
            data=form,
            headers={"Key": api_key, "User-Agent": USER_AGENT},
            timeout=timeout,
        ) as resp:
            text = await resp.text()
            try:
                payload = json.loads(text) if text else {}
            except json.JSONDecodeError:
                payload = {}
            return resp.status, text, payload

    @bot.command(
        name="ezupload",
        usage="[url] | key <api_key> | help",
        description="Upload files to e-z.gg hosting",
    )
    async def ezupload_cmd(ctx, *, args: str = ""):
        raw = (args or "").strip()
        parts = raw.split(maxsplit=1)
        sub = parts[0].lower() if parts else ""

        if sub in ("help", "?"):
            await ctx.message.delete()
            prefix = getConfigData().get("prefix", "<p>")
            await send_temp(
                ctx,
                f"**`{prefix}ezupload`** — attach a file, pass a URL, or `{prefix}ezupload key <api_key>`",
            )
            return

        if sub in ("key", "setkey"):
            await ctx.message.delete()
            key = parts[1].strip() if len(parts) > 1 else ""
            if not key:
                await send_temp(ctx, "Usage: `<p>ezupload key <api_key>`")
                return
            updateConfigData(CONFIG_KEY, key)
            script_log("API key saved.", "SUCCESS")
            tail = key[-4:] if len(key) >= 4 else "****"
            await send_temp(ctx, f"e-z.gg API key saved (ends with `{tail}`).")
            return

        attachment = ctx.message.attachments[0] if ctx.message.attachments else None
        file_data = None
        filename = None
        header_type = ""

        if attachment:
            if attachment.size > MAX_SIZE:
                await ctx.message.delete()
                await send_temp(ctx, "File too large. Maximum size is 100MB.")
                return
            try:
                file_data = await attachment.read()
            except Exception as e:
                await ctx.message.delete()
                script_log(f"Failed to read attachment: {e}", "ERROR")
                await send_temp(ctx, f"Could not read attachment: {e}")
                return
            filename = attachment.filename
            header_type = getattr(attachment, "content_type", "") or ""

        try:
            await ctx.message.delete()
        except Exception:
            pass

        api_key = getConfigData().get(CONFIG_KEY, "")
        if not api_key:
            await send_temp(ctx, "No API key set. Use `<p>ezupload key <api_key>`.")
            return

        source_url = raw if (not attachment and raw) else ""
        if not attachment and not source_url:
            await send_temp(ctx, "Attach a file or provide a URL to upload.")
            return

        status_msg = await ctx.send("Uploading...", silent=True)
        try:
            async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session:
                if source_url:
                    try:
                        file_data, filename, header_type = await download_url(session, source_url)
                    except ValueError:
                        await send_temp(ctx, "File too large. Maximum size is 100MB.")
                        return
                    except Exception as e:
                        script_log(f"Download failed: {e}", "ERROR")
                        await send_temp(ctx, f"Could not download file: {e}")
                        return

                content_type = content_type_for(filename, header_type)
                if not content_type:
                    await send_temp(
                        ctx,
                        "File type not supported. Only video, image, audio, and common application files are allowed.",
                    )
                    return

                try:
                    status, text, result = await upload_file(
                        session, api_key, filename, file_data, content_type
                    )
                except Exception as e:
                    script_log(f"Upload request failed: {e}", "ERROR")
                    await send_temp(ctx, f"Network error: {e}")
                    return

            if status != 200 or not result.get("success"):
                detail = result.get("message") or result.get("error") or text[:200] or f"HTTP {status}"
                script_log(f"Upload failed ({status}): {detail}", "ERROR")
                await send_temp(ctx, f"Upload failed ({status}): {detail}")
                return

            view_url = result_url(result, "imageUrl", "image_url", "url")
            raw_url = result_url(result, "rawUrl", "raw_url") or view_url
            delete_url = result_url(result, "deletionUrl", "deletion_url", "deleteUrl")
            kind = content_type.split("/", 1)[0]
            emoji = TYPE_EMOJI.get(kind, "📁")
            preview = raw_url if file_ext(filename) in IMAGE_EXTS else None

            links = []
            if view_url:
                links.append(f"🔗 [**View File**]({view_url})")
            if raw_url and raw_url != view_url:
                links.append(f"📝 [**Raw Content**]({raw_url})")
            if delete_url:
                links.append(f"🗑️ [**Delete File**]({delete_url})")

            await send_embed(
                ctx.channel.id,
                "E-Z.GG Upload Complete",
                (
                    f"# {emoji} File Uploaded Successfully!\n\n"
                    f"**Filename:** `{filename}`\n"
                    f"**Type:** `{content_type}`\n\n"
                    f"**Links:**\n" + "\n".join(links)
                ),
                image=preview,
            )
            script_log(f"Uploaded {filename}", "SUCCESS")
        finally:
            try:
                await status_msg.delete()
            except Exception:
                pass

ez_upload_script()
