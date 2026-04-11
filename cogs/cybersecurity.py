"""
Cybersecurity tools cog for DayZero Bot.

Provides IP/domain lookup, DNS records, CVE search, hash generation,
password strength analysis, subnet calculation, HTTP header inspection,
port reference, and reverse DNS.
"""

import hashlib
import ipaddress
import math
import re
import socket
import string

import aiohttp
import discord
from discord.ext import commands
class CyberSecurity(commands.Cog, name="Cybersecurity"):
    """Cybersecurity reconnaissance and utility commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    @commands.command(name="iplookup", aliases=["ip"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ip_lookup(self, ctx: commands.Context, target: str):
        """Look up geolocation and network info for an IP or domain.

        Usage: -iplookup <ip_or_domain>
        """
        url = f"http://ip-api.com/json/{target}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
        async with self.session.get(url) as resp:
            data = await resp.json()

        if data.get("status") == "fail":
            await ctx.send(f"Lookup failed: {data.get('message', 'unknown error')}")
            return

        embed = discord.Embed(title=f"IP Lookup: {data['query']}", color=0x00FF88)
        embed.add_field(name="Country", value=data.get("country", "N/A"))
        embed.add_field(name="Region", value=data.get("regionName", "N/A"))
        embed.add_field(name="City", value=data.get("city", "N/A"))
        embed.add_field(name="ZIP", value=data.get("zip", "N/A"))
        embed.add_field(name="Coords", value=f"{data.get('lat')}, {data.get('lon')}")
        embed.add_field(name="Timezone", value=data.get("timezone", "N/A"))
        embed.add_field(name="ISP", value=data.get("isp", "N/A"))
        embed.add_field(name="Org", value=data.get("org", "N/A"))
        embed.add_field(name="AS", value=data.get("as", "N/A"))
        embed.set_footer(text="Data from ip-api.com")
        await ctx.send(embed=embed)

    @commands.command(name="dns")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dns_lookup(self, ctx: commands.Context, domain: str, record_type: str = "A"):
        """Query DNS records for a domain using a public DNS-over-HTTPS resolver.

        Usage: -dns <domain> [record_type]
        Supported types: A, AAAA, MX, TXT, NS, CNAME, SOA
        """
        record_type = record_type.upper()
        valid = {"A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA"}
        if record_type not in valid:
            await ctx.send(f"Unsupported record type. Choose from: {', '.join(sorted(valid))}")
            return

        url = f"https://dns.google/resolve?name={domain}&type={record_type}"
        async with self.session.get(url) as resp:
            data = await resp.json()

        answers = data.get("Answer", [])
        if not answers:
            await ctx.send(f"No `{record_type}` records found for `{domain}`.")
            return

        lines = [f"`{a['data']}`  (TTL {a['TTL']}s)" for a in answers[:15]]
        embed = discord.Embed(
            title=f"DNS {record_type} Records: {domain}",
            description="\n".join(lines),
            color=0x3498DB,
        )
        embed.set_footer(text="Resolved via dns.google")
        await ctx.send(embed=embed)

    @commands.command(name="rdns", aliases=["reversedns"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def reverse_dns(self, ctx: commands.Context, ip: str):
        """Perform a reverse DNS lookup on an IP address.

        Usage: -rdns <ip_address>
        """
        try:
            host, _, _ = socket.gethostbyaddr(ip)
            await ctx.send(f"`{ip}` resolves to `{host}`")
        except socket.herror:
            await ctx.send(f"No reverse DNS entry found for `{ip}`.")
        except socket.gaierror:
            await ctx.send("Invalid IP address.")

    @commands.command(name="headers", aliases=["httpheaders"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def http_headers(self, ctx: commands.Context, url: str):
        """Inspect HTTP response headers from a URL (security header audit).

        Usage: -headers <url>
        """
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            async with self.session.head(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                headers = resp.headers
        except Exception as exc:
            await ctx.send(f"Could not reach `{url}`: {exc}")
            return

        security_headers = {
            "Strict-Transport-Security": headers.get("Strict-Transport-Security"),
            "Content-Security-Policy": headers.get("Content-Security-Policy"),
            "X-Content-Type-Options": headers.get("X-Content-Type-Options"),
            "X-Frame-Options": headers.get("X-Frame-Options"),
            "X-XSS-Protection": headers.get("X-XSS-Protection"),
            "Referrer-Policy": headers.get("Referrer-Policy"),
            "Permissions-Policy": headers.get("Permissions-Policy"),
            "Server": headers.get("Server"),
        }

        embed = discord.Embed(title=f"HTTP Headers: {url}", color=0xE74C3C)
        for name, value in security_headers.items():
            status = value if value else "**MISSING**"
            # Truncate long values
            if value and len(value) > 200:
                status = value[:200] + "..."
            embed.add_field(name=name, value=f"`{status}`", inline=False)

        present = sum(1 for v in security_headers.values() if v and v != headers.get("Server"))
        total = len(security_headers) - 1  # exclude Server from score
        embed.set_footer(text=f"Security headers present: {present}/{total}")
        await ctx.send(embed=embed)

    @commands.command(name="cve")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cve_lookup(self, ctx: commands.Context, cve_id: str):
        """Look up a CVE by its ID.

        Usage: -cve CVE-2024-1234
        """
        cve_id = cve_id.upper()
        if not re.match(r"^CVE-\d{4}-\d{4,}$", cve_id):
            await ctx.send("Invalid CVE ID format. Use `CVE-YYYY-NNNNN`.")
            return

        url = f"https://cveawg.mitre.org/api/cve/{cve_id}"
        async with self.session.get(url) as resp:
            if resp.status == 404:
                await ctx.send(f"`{cve_id}` not found.")
                return
            if resp.status != 200:
                await ctx.send(f"API error (HTTP {resp.status}).")
                return
            data = await resp.json()

        cna = data.get("containers", {}).get("cna", {})
        title = cna.get("title", "No title")
        descriptions = cna.get("descriptions", [])
        desc = descriptions[0]["value"] if descriptions else "No description available."
        if len(desc) > 800:
            desc = desc[:800] + "..."

        # Extract CVSS if available
        metrics = cna.get("metrics", [])
        cvss_text = "N/A"
        for m in metrics:
            for key in ("cvssV4_0", "cvssV3_1", "cvssV3_0", "cvssV2_0"):
                if key in m:
                    score = m[key].get("baseScore", "?")
                    severity = m[key].get("baseSeverity", "")
                    cvss_text = f"{score} ({severity})" if severity else str(score)
                    break

        affected = cna.get("affected", [])
        products = ", ".join(
            f"{a.get('vendor', '?')}/{a.get('product', '?')}" for a in affected[:5]
        ) or "N/A"

        embed = discord.Embed(title=f"{cve_id}: {title}", description=desc, color=0xFF5555)
        embed.add_field(name="CVSS", value=cvss_text, inline=True)
        embed.add_field(name="Affected", value=products, inline=True)
        embed.add_field(
            name="References",
            value=f"[NVD](https://nvd.nist.gov/vuln/detail/{cve_id}) | [MITRE](https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve_id})",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="hash")
    async def hash_text(self, ctx: commands.Context, algorithm: str, *, text: str):
        """Generate a hash of the given text.

        Usage: -hash <algorithm> <text>
        Algorithms: md5, sha1, sha256, sha512
        """
        algorithm = algorithm.lower()
        algos = {"md5": hashlib.md5, "sha1": hashlib.sha1, "sha256": hashlib.sha256, "sha512": hashlib.sha512}
        if algorithm not in algos:
            await ctx.send(f"Unsupported algorithm. Choose from: {', '.join(algos)}")
            return

        digest = algos[algorithm](text.encode()).hexdigest()
        embed = discord.Embed(title=f"{algorithm.upper()} Hash", color=0x9B59B6)
        embed.add_field(name="Input", value=f"```{text[:500]}```", inline=False)
        embed.add_field(name="Hash", value=f"```{digest}```", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="password", aliases=["passcheck", "pwcheck"])
    async def password_check(self, ctx: commands.Context, *, password: str):
        """Analyze password strength (the message is deleted for privacy).

        Usage: -password <your_password>
        """
        # Delete the invoking message so the password isn't left in chat
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        length = len(password)
        has_upper = bool(re.search(r"[A-Z]", password))
        has_lower = bool(re.search(r"[a-z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(re.search(r"[^A-Za-z0-9]", password))

        # Calculate entropy
        pool = 0
        if has_lower:
            pool += 26
        if has_upper:
            pool += 26
        if has_digit:
            pool += 10
        if has_special:
            pool += len(string.punctuation)
        entropy = length * math.log2(pool) if pool else 0

        # Common patterns
        issues = []
        if length < 8:
            issues.append("Too short (< 8 chars)")
        if not has_upper:
            issues.append("No uppercase letters")
        if not has_lower:
            issues.append("No lowercase letters")
        if not has_digit:
            issues.append("No digits")
        if not has_special:
            issues.append("No special characters")
        if re.search(r"(.)\1{2,}", password):
            issues.append("Contains repeated characters")
        if re.search(r"(012|123|234|345|456|567|678|789|abc|bcd|cde|def)", password.lower()):
            issues.append("Contains sequential characters")

        # Rating
        if entropy >= 60 and not issues:
            rating, color = "Strong", 0x2ECC71
        elif entropy >= 40 and len(issues) <= 2:
            rating, color = "Moderate", 0xF39C12
        else:
            rating, color = "Weak", 0xE74C3C

        embed = discord.Embed(title="Password Strength Analysis", color=color)
        embed.add_field(name="Rating", value=f"**{rating}**", inline=True)
        embed.add_field(name="Length", value=str(length), inline=True)
        embed.add_field(name="Entropy", value=f"{entropy:.1f} bits", inline=True)
        embed.add_field(
            name="Character Sets",
            value=f"{'Uppercase ' if has_upper else ''}{'Lowercase ' if has_lower else ''}"
                  f"{'Digits ' if has_digit else ''}{'Symbols' if has_special else ''}",
            inline=False,
        )
        if issues:
            embed.add_field(name="Issues", value="\n".join(f"- {i}" for i in issues), inline=False)
        embed.set_footer(text="Your message was deleted for privacy.")
        await ctx.send(embed=embed)

    @commands.command(name="subnet", aliases=["cidr"])
    async def subnet_calc(self, ctx: commands.Context, cidr: str):
        """Calculate subnet information from CIDR notation.

        Usage: -subnet 192.168.1.0/24
        """
        try:
            net = ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            await ctx.send("Invalid CIDR notation. Example: `192.168.1.0/24`")
            return

        embed = discord.Embed(title=f"Subnet: {net}", color=0x1ABC9C)
        embed.add_field(name="Network Address", value=str(net.network_address))
        embed.add_field(name="Broadcast", value=str(net.broadcast_address))
        embed.add_field(name="Netmask", value=str(net.netmask))
        embed.add_field(name="Wildcard", value=str(net.hostmask))
        embed.add_field(name="Prefix Length", value=f"/{net.prefixlen}")
        embed.add_field(name="Total Hosts", value=f"{net.num_addresses:,}")
        embed.add_field(name="Usable Hosts", value=f"{max(net.num_addresses - 2, 0):,}")
        embed.add_field(name="Is Private", value=str(net.is_private))
        # Show first/last usable host
        hosts = list(net.hosts())
        if hosts:
            embed.add_field(name="Host Range", value=f"`{hosts[0]}` - `{hosts[-1]}`")
        await ctx.send(embed=embed)

    @commands.command(name="port", aliases=["ports"])
    async def port_info(self, ctx: commands.Context, port: int = None):
        """Look up common port numbers or show info for a specific port.

        Usage: -port [port_number]
        """
        port_db = {
            20: ("FTP Data", "File Transfer Protocol - Data"),
            21: ("FTP Control", "File Transfer Protocol - Control"),
            22: ("SSH", "Secure Shell"),
            23: ("Telnet", "Unencrypted remote login (insecure)"),
            25: ("SMTP", "Simple Mail Transfer Protocol"),
            53: ("DNS", "Domain Name System"),
            67: ("DHCP Server", "Dynamic Host Configuration Protocol"),
            68: ("DHCP Client", "Dynamic Host Configuration Protocol"),
            69: ("TFTP", "Trivial File Transfer Protocol"),
            80: ("HTTP", "Hypertext Transfer Protocol"),
            110: ("POP3", "Post Office Protocol v3"),
            119: ("NNTP", "Network News Transfer Protocol"),
            123: ("NTP", "Network Time Protocol"),
            135: ("MSRPC", "Microsoft RPC"),
            137: ("NetBIOS-NS", "NetBIOS Name Service"),
            139: ("NetBIOS-SSN", "NetBIOS Session Service"),
            143: ("IMAP", "Internet Message Access Protocol"),
            161: ("SNMP", "Simple Network Management Protocol"),
            162: ("SNMP Trap", "SNMP Trap"),
            389: ("LDAP", "Lightweight Directory Access Protocol"),
            443: ("HTTPS", "HTTP Secure (TLS/SSL)"),
            445: ("SMB", "Server Message Block"),
            465: ("SMTPS", "SMTP over SSL"),
            514: ("Syslog", "System Logging"),
            587: ("SMTP Submission", "Email message submission"),
            636: ("LDAPS", "LDAP over SSL"),
            993: ("IMAPS", "IMAP over SSL"),
            995: ("POP3S", "POP3 over SSL"),
            1433: ("MSSQL", "Microsoft SQL Server"),
            1521: ("Oracle DB", "Oracle Database"),
            3306: ("MySQL", "MySQL Database"),
            3389: ("RDP", "Remote Desktop Protocol"),
            5432: ("PostgreSQL", "PostgreSQL Database"),
            5900: ("VNC", "Virtual Network Computing"),
            6379: ("Redis", "Redis Database"),
            8080: ("HTTP Alt", "HTTP Alternate / Proxy"),
            8443: ("HTTPS Alt", "HTTPS Alternate"),
            27017: ("MongoDB", "MongoDB Database"),
        }

        if port is not None:
            info = port_db.get(port)
            if info:
                embed = discord.Embed(title=f"Port {port}: {info[0]}", description=info[1], color=0x3498DB)
            else:
                embed = discord.Embed(
                    title=f"Port {port}",
                    description="Not in the common ports database. It may be a custom or ephemeral port.",
                    color=0x95A5A6,
                )
            await ctx.send(embed=embed)
            return

        # Show all common ports
        lines = [f"`{p:>5}` | **{info[0]}** - {info[1]}" for p, info in sorted(port_db.items())]
        # Split into chunks to fit embed limits
        chunk_size = 20
        for i in range(0, len(lines), chunk_size):
            embed = discord.Embed(
                title="Common Ports Reference" if i == 0 else "Common Ports (continued)",
                description="\n".join(lines[i:i + chunk_size]),
                color=0x3498DB,
            )
            await ctx.send(embed=embed)

    @commands.command(name="whois")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def whois_lookup(self, ctx: commands.Context, domain: str):
        """Get WHOIS information for a domain.

        Usage: -whois example.com
        """
        url = f"https://da.gd/w/{domain}"
        async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            text = await resp.text()

        if not text or "No match" in text:
            await ctx.send(f"No WHOIS data found for `{domain}`.")
            return

        # Truncate if too long
        if len(text) > 3900:
            text = text[:3900] + "\n... (truncated)"

        embed = discord.Embed(title=f"WHOIS: {domain}", description=f"```\n{text}\n```", color=0xE67E22)
        await ctx.send(embed=embed)

    @commands.command(name="portcheck")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def port_check(self, ctx: commands.Context, host: str, port: int):
        """Check if a specific port is open on a host (TCP connect test).

        Usage: -portcheck <host> <port>
        Note: Only works on hosts that allow connections.
        """
        if port < 1 or port > 65535:
            await ctx.send("Port must be between 1 and 65535.")
            return

        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=5
            )
            writer.close()
            await writer.wait_closed()
            status = "OPEN"
            color = 0x2ECC71
        except (asyncio.TimeoutError, OSError):
            status = "CLOSED / FILTERED"
            color = 0xE74C3C

        embed = discord.Embed(title=f"Port Check: {host}:{port}", color=color)
        embed.add_field(name="Status", value=f"**{status}**")
        await ctx.send(embed=embed)
async def setup(bot: commands.Bot):
    await bot.add_cog(CyberSecurity(bot))
