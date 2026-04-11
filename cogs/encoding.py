"""
Encoding and decoding tools cog for DayZero Bot.

Provides base64, hex, URL, ROT13, binary, morse code, and Caesar cipher
encoding/decoding utilities useful for CTF challenges and general cybersecurity work.
"""

import base64
import binascii
import urllib.parse

import discord
from discord.ext import commands

MORSE_CODE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..", "0": "-----", "1": ".----", "2": "..---", "3": "...--",
    "4": "....-", "5": ".....", "6": "-....", "7": "--...", "8": "---..",
    "9": "----.", " ": "/", ".": ".-.-.-", ",": "--..--", "?": "..--..",
    "!": "-.-.--", "'": ".----.", "/": "-..-.", "(": "-.--.",
    ")": "-.--.-", "&": ".-...", ":": "---...", ";": "-.-.-.",
    "=": "-...-", "+": ".-.-.", "-": "-....-", "_": "..--.-",
    '"': ".-..-.", "$": "...-..-", "@": ".--.-.",
}
MORSE_REVERSE = {v: k for k, v in MORSE_CODE.items()}
class Encoding(commands.Cog, name="Encoding"):
    """Encoding, decoding, and cipher tools for CTFs and security work."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _embed(title: str, input_text: str, output_text: str, color: int = 0x9B59B6) -> discord.Embed:
        embed = discord.Embed(title=title, color=color)
        embed.add_field(name="Input", value=f"```{input_text[:500]}```", inline=False)
        embed.add_field(name="Output", value=f"```{output_text[:1500]}```", inline=False)
        return embed

    @commands.command(name="b64encode", aliases=["b64e"])
    async def base64_encode(self, ctx: commands.Context, *, text: str):
        """Encode text to Base64.

        Usage: -b64encode <text>
        """
        encoded = base64.b64encode(text.encode()).decode()
        await ctx.send(embed=self._embed("Base64 Encode", text, encoded))

    @commands.command(name="b64decode", aliases=["b64d"])
    async def base64_decode(self, ctx: commands.Context, *, text: str):
        """Decode Base64 to text.

        Usage: -b64decode <base64_string>
        """
        try:
            decoded = base64.b64decode(text).decode("utf-8", errors="replace")
        except (binascii.Error, ValueError):
            await ctx.send("Invalid Base64 input.")
            return
        await ctx.send(embed=self._embed("Base64 Decode", text, decoded))

    @commands.command(name="hexencode", aliases=["hexe", "tohex"])
    async def hex_encode(self, ctx: commands.Context, *, text: str):
        """Encode text to hexadecimal.

        Usage: -hexencode <text>
        """
        encoded = text.encode().hex()
        await ctx.send(embed=self._embed("Hex Encode", text, encoded))

    @commands.command(name="hexdecode", aliases=["hexd", "fromhex"])
    async def hex_decode(self, ctx: commands.Context, *, text: str):
        """Decode hexadecimal to text.

        Usage: -hexdecode <hex_string>
        """
        cleaned = text.replace(" ", "").replace("0x", "")
        try:
            decoded = bytes.fromhex(cleaned).decode("utf-8", errors="replace")
        except ValueError:
            await ctx.send("Invalid hex input.")
            return
        await ctx.send(embed=self._embed("Hex Decode", text, decoded))

    @commands.command(name="urlencode", aliases=["urle"])
    async def url_encode(self, ctx: commands.Context, *, text: str):
        """URL-encode a string.

        Usage: -urlencode <text>
        """
        encoded = urllib.parse.quote(text, safe="")
        await ctx.send(embed=self._embed("URL Encode", text, encoded))

    @commands.command(name="urldecode", aliases=["urld"])
    async def url_decode(self, ctx: commands.Context, *, text: str):
        """URL-decode a string.

        Usage: -urldecode <encoded_text>
        """
        decoded = urllib.parse.unquote(text)
        await ctx.send(embed=self._embed("URL Decode", text, decoded))

    @commands.command(name="rot13")
    async def rot13(self, ctx: commands.Context, *, text: str):
        """Apply ROT13 to text (encode and decode are the same operation).

        Usage: -rot13 <text>
        """
        result = text.translate(
            str.maketrans(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
            )
        )
        await ctx.send(embed=self._embed("ROT13", text, result))

    @commands.command(name="caesar")
    async def caesar_cipher(self, ctx: commands.Context, shift: int, *, text: str):
        """Apply a Caesar cipher with a given shift.

        Usage: -caesar <shift> <text>
        Example: -caesar 3 hello world
        """
        result = []
        for ch in text:
            if ch.isalpha():
                base = ord("A") if ch.isupper() else ord("a")
                result.append(chr((ord(ch) - base + shift) % 26 + base))
            else:
                result.append(ch)
        output = "".join(result)
        await ctx.send(embed=self._embed(f"Caesar Cipher (shift {shift})", text, output))

    @commands.command(name="caesarbrute", aliases=["caesarall"])
    async def caesar_brute(self, ctx: commands.Context, *, text: str):
        """Brute-force all 25 Caesar cipher rotations.

        Usage: -caesarbrute <ciphertext>
        """
        lines = []
        for shift in range(1, 26):
            decrypted = []
            for ch in text:
                if ch.isalpha():
                    base = ord("A") if ch.isupper() else ord("a")
                    decrypted.append(chr((ord(ch) - base + shift) % 26 + base))
                else:
                    decrypted.append(ch)
            lines.append(f"ROT-{shift:>2}: {''.join(decrypted)}")

        output = "\n".join(lines)
        if len(output) > 3900:
            output = output[:3900] + "\n..."

        embed = discord.Embed(
            title="Caesar Brute Force",
            description=f"```\n{output}\n```",
            color=0x9B59B6,
        )
        await ctx.send(embed=embed)

    @commands.command(name="tobinary", aliases=["bin"])
    async def to_binary(self, ctx: commands.Context, *, text: str):
        """Convert text to binary representation.

        Usage: -tobinary <text>
        """
        binary = " ".join(format(ord(c), "08b") for c in text)
        await ctx.send(embed=self._embed("Text to Binary", text, binary))

    @commands.command(name="frombinary", aliases=["unbin"])
    async def from_binary(self, ctx: commands.Context, *, text: str):
        """Convert binary (space-separated bytes) back to text.

        Usage: -frombinary 01101000 01101001
        """
        try:
            chars = [chr(int(b, 2)) for b in text.split()]
            result = "".join(chars)
        except ValueError:
            await ctx.send("Invalid binary input. Use space-separated 8-bit groups.")
            return
        await ctx.send(embed=self._embed("Binary to Text", text, result))

    @commands.command(name="tomorse", aliases=["morse"])
    async def to_morse(self, ctx: commands.Context, *, text: str):
        """Convert text to Morse code.

        Usage: -tomorse <text>
        """
        result = " ".join(MORSE_CODE.get(c.upper(), "?") for c in text)
        await ctx.send(embed=self._embed("Text to Morse", text, result))

    @commands.command(name="frommorse", aliases=["unmorse"])
    async def from_morse(self, ctx: commands.Context, *, text: str):
        """Convert Morse code back to text.

        Usage: -frommorse .... . .-.. .-.. ---
        Use / for spaces between words.
        """
        result = "".join(MORSE_REVERSE.get(code, "?") for code in text.split())
        await ctx.send(embed=self._embed("Morse to Text", text, result))

    @commands.command(name="analyze", aliases=["stranalysis"])
    async def string_analysis(self, ctx: commands.Context, *, text: str):
        """Analyze a string: length, char types, entropy, and detect encoding.

        Usage: -analyze <text>
        """
        import math
        import collections

        length = len(text)
        alpha = sum(c.isalpha() for c in text)
        digits = sum(c.isdigit() for c in text)
        spaces = sum(c.isspace() for c in text)
        special = length - alpha - digits - spaces

        # Shannon entropy
        freq = collections.Counter(text)
        entropy = -sum((count / length) * math.log2(count / length) for count in freq.values())

        # Detect likely encodings
        guesses = []
        if all(c in "0123456789abcdefABCDEF " for c in text.replace("0x", "")):
            guesses.append("Hex")
        try:
            base64.b64decode(text, validate=True)
            if len(text) % 4 == 0 and len(text) >= 4:
                guesses.append("Base64")
        except Exception:
            pass
        if all(c in "01 " for c in text) and len(text.replace(" ", "")) % 8 == 0:
            guesses.append("Binary")
        if all(c in ".-/ " for c in text):
            guesses.append("Morse")

        embed = discord.Embed(title="String Analysis", color=0xE91E63)
        embed.add_field(name="Length", value=str(length))
        embed.add_field(name="Alphabetic", value=str(alpha))
        embed.add_field(name="Digits", value=str(digits))
        embed.add_field(name="Spaces", value=str(spaces))
        embed.add_field(name="Special", value=str(special))
        embed.add_field(name="Entropy", value=f"{entropy:.2f} bits/char")
        embed.add_field(
            name="Possible Encodings",
            value=", ".join(guesses) if guesses else "None detected",
            inline=False,
        )
        embed.add_field(name="Preview", value=f"```{text[:300]}```", inline=False)
        await ctx.send(embed=embed)
async def setup(bot: commands.Bot):
    await bot.add_cog(Encoding(bot))
