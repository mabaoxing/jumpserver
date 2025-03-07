# -*- coding: utf-8 -*-
#
import re
import json
from six import string_types
import base64
import os
import time
import hashlib
from io import StringIO
from itertools import chain

import paramiko
import sshpubkeys
from itsdangerous import (
    TimedJSONWebSignatureSerializer, JSONWebSignatureSerializer,
    BadSignature, SignatureExpired
)
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields.files import FileField

from .http import http_date

UUID_PATTERN = re.compile(r'[0-9a-zA-Z\-]{36}')


class Singleton(type):
    def __init__(cls, *args, **kwargs):
        cls.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)
            return cls.__instance
        else:
            return cls.__instance


class Signer(metaclass=Singleton):
    """用来加密,解密,和基于时间戳的方式验证token"""

    def __init__(self, secret_key=None):
        self.secret_key = secret_key

    def sign(self, value):
        s = JSONWebSignatureSerializer(self.secret_key, algorithm_name='HS256')
        return s.dumps(value).decode()

    def unsign(self, value):
        if value is None:
            return value
        s = JSONWebSignatureSerializer(self.secret_key, algorithm_name='HS256')
        try:
            return s.loads(value)
        except BadSignature:
            return None

    def sign_t(self, value, expires_in=3600):
        s = TimedJSONWebSignatureSerializer(self.secret_key, expires_in=expires_in)
        return str(s.dumps(value), encoding="utf8")

    def unsign_t(self, value):
        s = TimedJSONWebSignatureSerializer(self.secret_key)
        try:
            return s.loads(value)
        except (BadSignature, SignatureExpired):
            return None


def ssh_key_string_to_obj(text, password=None):
    key = None
    try:
        key = paramiko.RSAKey.from_private_key(StringIO(text), password=password)
    except paramiko.SSHException:
        pass
    else:
        return key

    try:
        key = paramiko.DSSKey.from_private_key(StringIO(text), password=password)
    except paramiko.SSHException:
        pass
    else:
        return key

    return key


def ssh_private_key_gen(private_key, password=None):
    if isinstance(private_key, bytes):
        private_key = private_key.decode("utf-8")
    if isinstance(private_key, string_types):
        private_key = ssh_key_string_to_obj(private_key, password=password)
    return private_key


def ssh_pubkey_gen(private_key=None, username='jumpserver', hostname='localhost', password=None):
    private_key = ssh_private_key_gen(private_key, password=password)
    if not isinstance(private_key, (paramiko.RSAKey, paramiko.DSSKey)):
        raise IOError('Invalid private key')

    public_key = "%(key_type)s %(key_content)s %(username)s@%(hostname)s" % {
        'key_type': private_key.get_name(),
        'key_content': private_key.get_base64(),
        'username': username,
        'hostname': hostname,
    }
    return public_key


def ssh_key_gen(length=2048, type='rsa', password=None, username='jumpserver', hostname=None):
    """Generate user ssh private and public key

    Use paramiko RSAKey generate it.
    :return private key str and public key str
    """

    if hostname is None:
        hostname = os.uname()[1]

    f = StringIO()
    try:
        if type == 'rsa':
            private_key_obj = paramiko.RSAKey.generate(length)
        elif type == 'dsa':
            private_key_obj = paramiko.DSSKey.generate(length)
        else:
            raise IOError('SSH private key must be `rsa` or `dsa`')
        private_key_obj.write_private_key(f, password=password)
        private_key = f.getvalue()
        public_key = ssh_pubkey_gen(private_key_obj, username=username, hostname=hostname)
        return private_key, public_key
    except IOError:
        raise IOError('These is error when generate ssh key.')


def validate_ssh_private_key(text, password=None):
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except UnicodeDecodeError:
            return False

    key = ssh_key_string_to_obj(text, password=password)
    if key is None:
        return False
    else:
        return True


def validate_ssh_public_key(text):
    ssh = sshpubkeys.SSHKey(text)
    try:
        ssh.parse()
    except (sshpubkeys.InvalidKeyException, UnicodeDecodeError):
        return False
    except NotImplementedError as e:
        return False
    return True


def content_md5(data):
    """计算data的MD5值，经过Base64编码并返回str类型。

    返回值可以直接作为HTTP Content-Type头部的值
    """
    if isinstance(data, str):
        data = hashlib.md5(data.encode('utf-8'))
    value = base64.b64encode(data.hexdigest().encode('utf-8'))
    return value.decode('utf-8')


def make_signature(access_key_secret, date=None):
    if isinstance(date, bytes):
        date = bytes.decode(date)
    if isinstance(date, int):
        date_gmt = http_date(date)
    elif date is None:
        date_gmt = http_date(int(time.time()))
    else:
        date_gmt = date

    data = str(access_key_secret) + "\n" + date_gmt
    return content_md5(data)


def encrypt_password(password, salt=None, algorithm='sha512'):
    from passlib.hash import sha512_crypt, des_crypt

    def sha512():
        return sha512_crypt.using(rounds=5000).hash(password, salt=salt)

    def des():
        return des_crypt.hash(password, salt=salt[:2])

    support_algorithm = {
        'sha512': sha512, 'des': des
    }

    if isinstance(algorithm, str):
        algorithm = algorithm.lower()

    if algorithm not in support_algorithm.keys():
        algorithm = 'sha512'

    if password and support_algorithm[algorithm]:
        return support_algorithm[algorithm]()
    return None


def get_signer():
    s = Signer(settings.SECRET_KEY)
    return s


signer = get_signer()


def ensure_last_char_is_ascii(data):
    remain = ''


secret_pattern = re.compile(r'password|secret|key', re.IGNORECASE)


def data_to_json(data, sort_keys=True, indent=2, cls=None):
    if cls is None:
        cls = DjangoJSONEncoder
    return json.dumps(data, sort_keys=sort_keys, indent=indent, cls=cls)
