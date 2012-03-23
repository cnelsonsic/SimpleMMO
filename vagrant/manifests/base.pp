
group { "puppet":
  ensure => "present",
}

package { [
    'python-setuptools',
    'python-dev',
    'build-essential',
    'sqlite-3',
    'mongodb',
    ]:
    ensure => 'latest';
}


