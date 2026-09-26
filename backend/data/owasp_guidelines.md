# OWASP Secure Coding Guidelines & Remediation Strategies

## 1. Hardcoded Secrets
**Vulnerability Description:** Hardcoded secrets such as API keys, passwords, and tokens embedded directly in the source code can be easily discovered by attackers.
**Remediation Strategy:**
- NEVER hardcode secrets in source code.
- Always load sensitive credentials from environment variables or a secure vault at runtime.
- In Python, use `os.getenv("SECRET_KEY")` or similar configuration managers.
- Example Fix: Replace `password = "admin123"` with `import os; password = os.getenv("DB_PASSWORD")`.

## 2. SQL Injection (SQLi)
**Vulnerability Description:** SQL Injection occurs when untrusted user input is concatenated directly into database query strings, allowing attackers to manipulate queries.
**Remediation Strategy:**
- Use parameterized queries or prepared statements exclusively.
- Use Object-Relational Mapping (ORM) frameworks where applicable.
- Never use string formatting (e.g., f-strings in Python) to build SQL queries with user input.
- Example Fix: Replace `db.execute(f"SELECT * FROM users WHERE id = {user_id}")` with `db.execute("SELECT * FROM users WHERE id = ?", (user_id,))`.

## 3. Insecure Deserialization
**Vulnerability Description:** Deserializing untrusted data can lead to arbitrary code execution if the data contains malicious payloads. In Python, `pickle` is notoriously unsafe.
**Remediation Strategy:**
- Do not use `pickle` for untrusted data.
- Use safe serialization formats like JSON (`json.loads()`).
- If complex objects are needed, validate the schema strictly before processing.
- Example Fix: Replace `pickle.loads(data)` with `json.loads(data)`.

## 4. Cross-Site Scripting (XSS)
**Vulnerability Description:** XSS occurs when an application includes untrusted data in a web page without proper validation or escaping, allowing execution of malicious scripts.
**Remediation Strategy:**
- Always HTML-escape untrusted input before rendering it in the browser.
- Use modern templating engines (like Jinja2) that auto-escape variables by default.
- Example Fix: In templates, use `{{ user_input | escape }}` instead of rendering raw HTML.

## 5. Command Injection
**Vulnerability Description:** Command injection happens when user input is passed directly to system shells (e.g., `os.system()`, `subprocess.Popen(shell=True)`).
**Remediation Strategy:**
- Avoid calling OS commands directly if native libraries exist.
- If absolutely necessary, pass arguments as a list to `subprocess.run()`, NOT as a single string, and set `shell=False`.
- Example Fix: Replace `os.system(f"ping {ip}")` with `subprocess.run(["ping", ip])`.

## 6. Weak Cryptography
**Vulnerability Description:** Using outdated cryptographic algorithms (like MD5, SHA1) or weak random number generators makes encrypted data vulnerable.
**Remediation Strategy:**
- Use strong algorithms like AES-256 for encryption and SHA-256 or bcrypt for hashing.
- For random numbers in security contexts (like tokens), use cryptographically secure generators.
- Example Fix: Replace `random.randint()` with `secrets.randbelow()` for generating security tokens.
