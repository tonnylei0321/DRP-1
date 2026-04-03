"""密码哈希与验证工具（bcrypt 直接调用，兼容 bcrypt >= 4.0）。"""
import bcrypt


def hash_password(plain: str) -> str:
    """对明文密码进行 bcrypt 哈希。"""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """验证明文密码与哈希是否匹配。"""
    return bcrypt.checkpw(plain.encode(), hashed.encode())
