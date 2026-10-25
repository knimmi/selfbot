import discord
from discord.ext import commands
import random
import aiohttp
import asyncio
import io
import os
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter, ImageSequence
import imageio

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def log_err(self, ctx, e):
        if hasattr(self.bot, 'bot_logger'): self.bot.bot_logger.error(f"[{ctx.command.name}] {e}")

    # --- IMAGE UTILS ---
    async def get_image_url(self, ctx):
        if ctx.message.attachments: return ctx.message.attachments[0].url
        if ctx.message.reference:
            try:
                ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                if ref.attachments: return ref.attachments[0].url
            except: pass
        return None

    def fit_font(self, draw, text, img_w):
        target = int(img_w * 0.90)
        size = max(16, img_w // 5)
        while size > 10:
            try:
                font = ImageFont.truetype("arial.ttf", size)
            except:
                font = ImageFont.load_default()
            
            l, t, r, b = draw.textbbox((0, 0), text, font=font)
            if (r - l) <= target: return font
            size -= 2
        return font

    def outline_bubble(self, img, ocol=(0, 0, 0, 255), thk=2):
        mask = img.split()[3]
        outl_mask = mask.filter(ImageFilter.MaxFilter(thk * 2 + 1))
        outl_only = ImageChops.subtract(outl_mask, mask)
        outl_img = Image.new("RGBA", img.size, ocol)
        outl_img.putalpha(outl_only)
        return Image.alpha_composite(outl_img, img)

    def process_caption(self, img_bytes, text):
        base_img = Image.open(io.BytesIO(img_bytes))
        font = self.fit_font(ImageDraw.Draw(base_img), text, base_img.width)
        l, t, r, b = ImageDraw.Draw(base_img).textbbox((0, 0), text, font=font)
        text_w, text_h = r - l, b - t
        bar_h = text_h + 26
        
        is_gif = getattr(base_img, "is_animated", False)
        frames = []
        durations = []
        
        for i in range(getattr(base_img, "n_frames", 1)):
            base_img.seek(i)
            frame = base_img.convert("RGBA")
            new_frame = Image.new("RGBA", (frame.width, frame.height + bar_h), (255, 255, 255, 255))
            new_frame.paste(frame, (0, bar_h), mask=frame if 'A' in frame.getbands() else None)
            draw = ImageDraw.Draw(new_frame)
            draw.text(((frame.width - text_w) // 2, (bar_h - text_h) // 2), text, font=font, fill=(0, 0, 0, 255))
            frames.append(new_frame)
            if is_gif: durations.append(frame.info.get("duration", 100))
            
        out = io.BytesIO()
        if is_gif:
            frames[0].save(out, format="GIF", save_all=True, append_images=frames[1:], duration=durations, loop=0, disposal=2)
            return out, "caption.gif"
        else:
            frames[0].save(out, format="PNG")
            return out, "caption.png"

    def process_bubble(self, img_bytes, bubble_bytes, to_gif):
        img = Image.open(io.BytesIO(img_bytes))
        bubble = Image.open(io.BytesIO(bubble_bytes)).convert("RGBA").resize(img.size, Image.BICUBIC)
        bubble = self.outline_bubble(bubble)
        
        out = io.BytesIO()
        is_gif = getattr(img, "is_animated", False)
        
        if is_gif or to_gif:
            frames = []
            durations = []
            for frame in ImageSequence.Iterator(img):
                frames.append(Image.alpha_composite(frame.convert("RGBA"), bubble))
                durations.append(frame.info.get("duration", 100))
            frames[0].save(out, format="GIF", save_all=True, append_images=frames[1:], duration=durations, loop=0, disposal=2)
            return out, "bubble.gif"
        else:
            res = Image.alpha_composite(img.convert("RGBA"), bubble)
            res.save(out, format="PNG")
            return out, "bubble.png"

    @commands.command()
    async def caption(self, ctx, *, text: str):
        try: await ctx.message.delete()
        except: pass
        
        url = await self.get_image_url(ctx)
        if not url: return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Attach or reply to an image.**")
        
        status = await ctx.send(f"{self.bot.custom_emojis.get('loading', '')} Generating caption...")
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url) as r: img_bytes = await r.read()
            
            out, fname = await asyncio.to_thread(self.process_caption, img_bytes, text)
            out.seek(0)
            
            await ctx.send(file=discord.File(out, filename=fname))
            await status.delete()
        except Exception as e:
            self.log_err(ctx, e)
            await status.edit(content=f"{self.bot.custom_emojis.get('error', '')} **Generation failed.**")

    @commands.command()
    async def speechbubble(self, ctx, to_gif: str = ""):
        try: await ctx.message.delete()
        except: pass
        
        url = await self.get_image_url(ctx)
        if not url: return await ctx.send(f"{self.bot.custom_emojis.get('error', '')} **Attach or reply to an image.**")
        
        status = await ctx.send(f"{self.bot.custom_emojis.get('loading', '')} Adding speech bubble...")
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url) as r: img_bytes = await r.read()
                async with s.get("https://github.com/adambala/speech-bubble-it/blob/main/assets/speech_bubble.png?raw=true") as rb: 
                    bubble_bytes = await rb.read()
            
            out, fname = await asyncio.to_thread(self.process_bubble, img_bytes, bubble_bytes, bool(to_gif))
            out.seek(0)
            
            await ctx.send(file=discord.File(out, filename=fname))
            await status.delete()
        except Exception as e:
            self.log_err(ctx, e)
            await status.edit(content=f"{self.bot.custom_emojis.get('error', '')} **Generation failed.**")

    @commands.command()
    async def joke(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get("https://official-joke-api.appspot.com/random_joke") as r:
                    data = await r.json()
                    await ctx.send(f"**{data['setup']}**\n||{data['punchline']}||")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def meme(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get("https://meme-api.com/gimme") as r:
                    data = await r.json()
                    await ctx.send(data['url'])
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def name(self, ctx, *, target: str):
        try: await ctx.message.delete()
        except: pass
        try:
            num = random.randint(1, 100)
            await ctx.send(f"**{target}** is `{num}%` gay 🏳️‍🌈")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def nitro(self, ctx):
        try: await ctx.message.delete()
        except: pass
        try:
            code = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", k=16))
            await ctx.send(f"discord.gift/{code}")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def checkprofile(self, ctx, user: discord.Member):
        try: await ctx.message.delete()
        except: pass
        try: await ctx.send(f"**{user.name}** has `{random.randint(1, 99)}` infractions.")
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def blurpify(self, ctx, user: discord.Member = None):
        try: await ctx.message.delete()
        except: pass
        target = user or ctx.author
        try:
            avatar = target.display_avatar.url
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://nekobot.xyz/api/imagegen?type=blurpify&image={avatar}") as r:
                    res = await r.json()
                    await ctx.send(res['message'])
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def deepfry(self, ctx, user: discord.Member = None):
        try: await ctx.message.delete()
        except: pass
        target = user or ctx.author
        try:
            avatar = target.display_avatar.url
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://nekobot.xyz/api/imagegen?type=deepfry&image={avatar}") as r:
                    res = await r.json()
                    await ctx.send(res['message'])
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def captcha(self, ctx, user: discord.Member = None):
        try: await ctx.message.delete()
        except: pass
        target = user or ctx.author
        try:
            avatar = target.display_avatar.url
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://nekobot.xyz/api/imagegen?type=captcha&url={avatar}&username={target.name}") as r:
                    res = await r.json()
                    await ctx.send(res['message'])
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def threat(self, ctx, user: discord.Member = None):
        try: await ctx.message.delete()
        except: pass
        target = user or ctx.author
        try:
            avatar = target.display_avatar.url
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://nekobot.xyz/api/imagegen?type=threats&url={avatar}") as r:
                    res = await r.json()
                    await ctx.send(res['message'])
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def iphone(self, ctx, user: discord.Member = None):
        try: await ctx.message.delete()
        except: pass
        target = user or ctx.author
        try:
            avatar = target.display_avatar.url
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://nekobot.xyz/api/imagegen?type=iphone&url={avatar}") as r:
                    res = await r.json()
                    await ctx.send(res['message'])
        except Exception as e: self.log_err(ctx, e)

    @commands.command()
    async def ship(self, ctx, user: discord.Member):
        try: await ctx.message.delete()
        except: pass
        try:
            avatar1 = ctx.author.display_avatar.url
            avatar2 = user.display_avatar.url
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://nekobot.xyz/api/imagegen?type=ship&user1={avatar1}&user2={avatar2}") as r:
                    res = await r.json()
                    await ctx.send(res['message'])
        except Exception as e: self.log_err(ctx, e)

async def setup(bot):
    await bot.add_cog(Fun(bot))