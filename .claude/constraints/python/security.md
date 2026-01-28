# Python Security Considerations

> **This document defines mandatory security standards for Python projects.**
> All code must follow these security practices to prevent vulnerabilities.

## 1. Input Validation

### 1.1 Validate All External Input
```python
from pathlib import Path
import re
from typing import Any, Dict

def validate_filename(filename: str) -> Path:
    """Validate and sanitise filename to prevent path traversal.

    Args:
        filename: Filename to validate.

    Returns:
        Validated Path object.

    Raises:
        ValueError: If filename is invalid.

    Example:
        >>> validate_filename("data.csv")
        PosixPath('data.csv')
        >>> validate_filename("../etc/passwd")
        Traceback (most recent call last):
        ...
        ValueError: Invalid filename: ../etc/passwd
    """
    # Remove any path separators to prevent path traversal
    safe_name = Path(filename).name

    # Validate against allowed pattern
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', safe_name):
        raise ValueError(f"Invalid filename: {filename}")

    return Path(safe_name)

def validate_email(email: str) -> str:
    """Validate email format.

    Args:
        email: Email address to validate.

    Returns:
        Validated email address.

    Raises:
        ValueError: If email format is invalid.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email: {email}")
    return email

def validate_integer_range(
    value: Any,
    min_value: int,
    max_value: int,
    name: str = "value"
) -> int:
    """Validate integer is within range.

    Args:
        value: Value to validate.
        min_value: Minimum allowed value.
        max_value: Maximum allowed value.
        name: Name of the value for error messages.

    Returns:
        Validated integer.

    Raises:
        TypeError: If value is not an integer.
        ValueError: If value is out of range.
    """
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, got {type(value)}")

    if value < min_value or value > max_value:
        raise ValueError(
            f"{name} must be between {min_value} and {max_value}, got {value}"
        )

    return value
```

### 1.2 Sanitise User Input
```python
import html
from urllib.parse import quote, unquote

def sanitise_html(text: str) -> str:
    """Sanitise text for HTML output to prevent XSS.

    Args:
        text: Text to sanitise.

    Returns:
        Sanitised text safe for HTML output.
    """
    return html.escape(text)

def sanitise_url_parameter(param: str) -> str:
    """Sanitise URL parameter.

    Args:
        param: URL parameter to sanitise.

    Returns:
        Sanitised URL parameter.
    """
    return quote(param, safe='')

def validate_json_input(data: str) -> Dict[str, Any]:
    """Validate and parse JSON input safely.

    Args:
        data: JSON string to parse.

    Returns:
        Parsed JSON data.

    Raises:
        ValueError: If JSON is invalid or too large.
    """
    # Limit input size to prevent DoS
    MAX_JSON_SIZE = 1024 * 1024  # 1MB
    if len(data) > MAX_JSON_SIZE:
        raise ValueError(f"JSON input too large: {len(data)} bytes")

    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e
```

## 2. Secrets Management

### 2.1 Never Hardcode Secrets
```python
import os
from pathlib import Path
from typing import Dict

# Bad: Hardcoded secrets (FORBIDDEN)
API_KEY = "sk-1234567890abcdef"  # NEVER do this
DATABASE_PASSWORD = "password123"  # NEVER do this

# Good: Load secrets from environment variables
API_KEY = os.environ.get('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")

DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')
if not DATABASE_PASSWORD:
    raise ValueError("DATABASE_PASSWORD environment variable not set")

# Good: Load from secure file
def load_secrets(secrets_file: Path) -> Dict[str, str]:
    """Load secrets from file outside repository.

    Args:
        secrets_file: Path to secrets file.

    Returns:
        Dictionary of secrets.

    Raises:
        FileNotFoundError: If secrets file not found.
        PermissionError: If secrets file has insecure permissions.
    """
    if not secrets_file.exists():
        raise FileNotFoundError(f"Secrets file not found: {secrets_file}")

    # Ensure file has restrictive permissions (Unix only)
    if hasattr(os, 'stat'):
        mode = secrets_file.stat().st_mode
        if mode & 0o077:
            raise PermissionError(
                f"Secrets file has insecure permissions: {secrets_file}"
            )

    # Load secrets
    with open(secrets_file) as f:
        return json.load(f)
```

### 2.2 Environment Variables
```python
import os
from typing import Optional

def get_secret(name: str, default: Optional[str] = None) -> str:
    """Get secret from environment variable.

    Args:
        name: Environment variable name.
        default: Default value if not set.

    Returns:
        Secret value.

    Raises:
        ValueError: If secret not found and no default provided.
    """
    value = os.environ.get(name, default)
    if value is None:
        raise ValueError(f"Secret not found: {name}")
    return value

# Usage
API_KEY = get_secret('API_KEY')
DATABASE_URL = get_secret('DATABASE_URL')
DEBUG_MODE = get_secret('DEBUG_MODE', 'false').lower() == 'true'
```

### 2.3 .env Files (Development Only)
```python
from pathlib import Path
from typing import Dict

def load_env_file(env_file: Path = Path('.env')) -> Dict[str, str]:
    """Load environment variables from .env file (development only).

    Args:
        env_file: Path to .env file.

    Returns:
        Dictionary of environment variables.

    Note:
        This should only be used in development. Production should use
        proper secret management systems.
    """
    if not env_file.exists():
        return {}

    env_vars = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    return env_vars

# .gitignore MUST include .env files
# .env
# .env.local
# .env.*.local
```

## 3. SQL Injection Prevention

### 3.1 Use Parameterised Queries
```python
import sqlite3
from typing import Optional, Dict, List

# Good: Parameterised queries
def get_user(conn: sqlite3.Connection, user_id: int) -> Optional[Dict]:
    """Get user by ID using parameterised query.

    Args:
        conn: Database connection.
        user_id: User ID.

    Returns:
        User data or None if not found.
    """
    cursor = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )
    return cursor.fetchone()

def search_users(
    conn: sqlite3.Connection,
    name: str,
    email: str
) -> List[Dict]:
    """Search users by name and email.

    Args:
        conn: Database connection.
        name: User name to search.
        email: User email to search.

    Returns:
        List of matching users.
    """
    cursor = conn.execute(
        "SELECT * FROM users WHERE name LIKE ? AND email LIKE ?",
        (f"%{name}%", f"%{email}%")
    )
    return cursor.fetchall()

# Bad: String formatting (SQL injection risk - FORBIDDEN)
def get_user_bad(conn: sqlite3.Connection, user_id: int) -> Optional[Dict]:
    """UNSAFE: Vulnerable to SQL injection."""
    cursor = conn.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchone()

# Bad: String concatenation (SQL injection risk - FORBIDDEN)
def search_users_bad(conn: sqlite3.Connection, name: str) -> List[Dict]:
    """UNSAFE: Vulnerable to SQL injection."""
    query = "SELECT * FROM users WHERE name = '" + name + "'"
    cursor = conn.execute(query)
    return cursor.fetchall()
```

### 3.2 Using ORMs Safely
```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    """User model."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)

# Good: ORM with parameterised queries
def get_user_by_email(session, email: str) -> Optional[User]:
    """Get user by email using ORM.

    Args:
        session: SQLAlchemy session.
        email: User email.

    Returns:
        User object or None.
    """
    return session.query(User).filter(User.email == email).first()

# Good: ORM with multiple filters
def search_users_orm(session, name: str, min_id: int) -> List[User]:
    """Search users using ORM.

    Args:
        session: SQLAlchemy session.
        name: User name pattern.
        min_id: Minimum user ID.

    Returns:
        List of matching users.
    """
    return session.query(User).filter(
        User.name.like(f"%{name}%"),
        User.id >= min_id
    ).all()
```

## 4. Path Traversal Prevention

### 4.1 Validate File Paths
```python
from pathlib import Path
from typing import Optional

def safe_join(base_dir: Path, *paths: str) -> Path:
    """Safely join paths preventing traversal outside base directory.

    Args:
        base_dir: Base directory.
        *paths: Path components to join.

    Returns:
        Safe joined path.

    Raises:
        ValueError: If resulting path is outside base directory.
    """
    base_dir = base_dir.resolve()
    full_path = (base_dir / Path(*paths)).resolve()

    # Ensure the resolved path is within base directory
    if not str(full_path).startswith(str(base_dir)):
        raise ValueError(f"Path traversal detected: {full_path}")

    return full_path

def read_user_file(base_dir: Path, filename: str) -> str:
    """Read user file safely.

    Args:
        base_dir: Base directory for user files.
        filename: Filename to read.

    Returns:
        File contents.

    Raises:
        ValueError: If path traversal detected.
        FileNotFoundError: If file not found.
    """
    # Validate filename
    safe_filename = validate_filename(filename)

    # Safely join paths
    file_path = safe_join(base_dir, str(safe_filename))

    # Read file
    return file_path.read_text()

# Bad: Unsafe path joining (FORBIDDEN)
def read_user_file_bad(base_dir: Path, filename: str) -> str:
    """UNSAFE: Vulnerable to path traversal."""
    file_path = base_dir / filename  # No validation
    return file_path.read_text()
```

## 5. Command Injection Prevention

### 5.1 Avoid Shell Execution
```python
import subprocess
from typing import List

# Good: Use list arguments without shell
def run_command(command: List[str]) -> str:
    """Run command safely without shell.

    Args:
        command: Command and arguments as list.

    Returns:
        Command output.

    Raises:
        subprocess.CalledProcessError: If command fails.
    """
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
        shell=False  # IMPORTANT: Never use shell=True with user input
    )
    return result.stdout

# Good: Validate command arguments
def run_git_command(args: List[str]) -> str:
    """Run git command safely.

    Args:
        args: Git command arguments.

    Returns:
        Command output.

    Raises:
        ValueError: If arguments contain suspicious characters.
    """
    # Validate arguments
    for arg in args:
        if any(char in arg for char in [';', '|', '&', '$', '`']):
            raise ValueError(f"Suspicious character in argument: {arg}")

    command = ['git'] + args
    return run_command(command)

# Bad: Using shell=True with user input (FORBIDDEN)
def run_command_bad(user_input: str) -> str:
    """UNSAFE: Vulnerable to command injection."""
    result = subprocess.run(
        f"ls {user_input}",  # NEVER do this
        shell=True,  # DANGEROUS with user input
        capture_output=True,
        text=True
    )
    return result.stdout
```

## 6. Cryptography

### 6.1 Use Strong Cryptography
```python
import hashlib
import secrets
from typing import Tuple

def hash_password(password: str) -> Tuple[str, str]:
    """Hash password using strong algorithm.

    Args:
        password: Password to hash.

    Returns:
        Tuple of (salt, hashed_password).
    """
    # Generate random salt
    salt = secrets.token_hex(32)

    # Hash password with salt using strong algorithm
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )

    return salt, hashed.hex()

def verify_password(
    password: str,
    salt: str,
    hashed_password: str
) -> bool:
    """Verify password against hash.

    Args:
        password: Password to verify.
        salt: Salt used for hashing.
        hashed_password: Hashed password to compare.

    Returns:
        True if password matches, False otherwise.
    """
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )

    return hashed.hex() == hashed_password

# Good: Generate secure random tokens
def generate_token(length: int = 32) -> str:
    """Generate secure random token.

    Args:
        length: Token length in bytes.

    Returns:
        Hex-encoded random token.
    """
    return secrets.token_hex(length)

# Bad: Weak hashing (FORBIDDEN)
def hash_password_bad(password: str) -> str:
    """UNSAFE: Weak hashing algorithm."""
    return hashlib.md5(password.encode()).hexdigest()  # NEVER use MD5
```

### 6.2 Use Cryptography Library
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64

def generate_key(password: str, salt: bytes) -> bytes:
    """Generate encryption key from password.

    Args:
        password: Password to derive key from.
        salt: Salt for key derivation.

    Returns:
        Encryption key.
    """
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_data(data: str, key: bytes) -> bytes:
    """Encrypt data using Fernet.

    Args:
        data: Data to encrypt.
        key: Encryption key.

    Returns:
        Encrypted data.
    """
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    """Decrypt data using Fernet.

    Args:
        encrypted_data: Encrypted data.
        key: Encryption key.

    Returns:
        Decrypted data.

    Raises:
        cryptography.fernet.InvalidToken: If decryption fails.
    """
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()
```

## 7. Secure File Operations

### 7.1 Secure File Permissions
```python
import os
from pathlib import Path

def create_secure_file(path: Path, content: str) -> None:
    """Create file with secure permissions.

    Args:
        path: File path.
        content: File content.
    """
    # Create file with restrictive permissions (owner read/write only)
    path.touch(mode=0o600)
    path.write_text(content)

def ensure_secure_permissions(path: Path) -> None:
    """Ensure file has secure permissions.

    Args:
        path: File path.

    Raises:
        PermissionError: If file has insecure permissions.
    """
    if not path.exists():
        return

    # Check permissions (Unix only)
    if hasattr(os, 'stat'):
        mode = path.stat().st_mode
        if mode & 0o077:  # Check if group/other have any permissions
            raise PermissionError(
                f"File has insecure permissions: {path} ({oct(mode)})"
            )
```

## 8. Denial of Service Prevention

### 8.1 Limit Resource Usage
```python
from typing import Iterator

def read_large_file_safely(
    path: Path,
    max_size: int = 100 * 1024 * 1024  # 100MB
) -> Iterator[str]:
    """Read large file with size limit.

    Args:
        path: File path.
        max_size: Maximum file size in bytes.

    Yields:
        File lines.

    Raises:
        ValueError: If file exceeds size limit.
    """
    file_size = path.stat().st_size
    if file_size > max_size:
        raise ValueError(
            f"File too large: {file_size} bytes (max: {max_size})"
        )

    with open(path, 'r') as f:
        for line in f:
            yield line.strip()

def process_with_timeout(
    func: Callable,
    timeout: int = 30
) -> Any:
    """Execute function with timeout.

    Args:
        func: Function to execute.
        timeout: Timeout in seconds.

    Returns:
        Function result.

    Raises:
        TimeoutError: If function exceeds timeout.
    """
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError(f"Function exceeded timeout: {timeout}s")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        result = func()
    finally:
        signal.alarm(0)

    return result
```

## 9. Security Checklist

### 9.1 Pre-Commit Security Checks
Before committing, verify:
- [ ] No hardcoded secrets or credentials
- [ ] All user input is validated
- [ ] SQL queries use parameterisation
- [ ] File paths are validated against traversal
- [ ] No shell=True with user input
- [ ] Strong cryptography is used
- [ ] File permissions are secure
- [ ] Resource limits are enforced
- [ ] Error messages don't leak sensitive information

## 10. Enforcement

### 10.1 Violations
**STRICTLY FORBIDDEN**:
- Hardcoding secrets or credentials
- Using shell=True with user input
- String formatting in SQL queries
- Using weak cryptography (MD5, SHA1 for passwords)
- Ignoring input validation
- Exposing sensitive information in error messages
- Using eval() or exec() on untrusted input

### 10.2 CI/CD Integration
All pull requests MUST:
- Pass security linting (bandit, safety)
- Have no hardcoded secrets
- Use parameterised queries
- Validate all external input
- Use strong cryptography