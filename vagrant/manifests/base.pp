
group { "puppet":
  ensure => "present",
}

# Install all our required packages.
package { [
    'git',
    'python-pip',
    'python-setuptools',
    'python-dev',
    'build-essential',
    'sqlite3',
    'mongodb',
    ]:
    ensure => 'latest';
}

# Pull down the source
exec { 'git clone git://github.com/cnelsonsic/SimpleMMO.git':
    cwd     => '/home/vagrant',
    path    => $::path,
    creates => '/home/vagrant/SimpleMMO/',
    refresh => 'cd /home/vagrant/SimpleMMO/; git pull',
    require => Package['git'],
}

# Install the requirements.
exec {'pip install --timeout=1 --use-mirrors -r requirements.txt':
    path    => $::path,
    cwd     => '/home/vagrant/SimpleMMO',
    tries   => 5, # Try really hard to install all the pip packages.
    require => [Package['python-pip'], Package['python-setuptools'], Package['python-dev'], Package['build-essential']],
}
