
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

# Stop the mongod service, SimpleMMO starts its own.
service { 'mongodb':
    name    => 'mongod',
    enable  => 'false',
    ensure  => 'stopped',
    require => Package['mongodb'],
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
# TODO: Install these one at a time instead of using the requirements file.
exec {'pip install --use-mirrors -r requirements.txt':
    path    => $::path,
    cwd     => '/home/vagrant/SimpleMMO',
    timeout => 0, # Turn off the timeout stuff. It might take longer than 5 minutes.
    tries   => 5, # Try really hard to install all the pip packages.
    logoutput => true,
    before  => Service['mongodb'], # Mongo tends to starve out pip. :(
    require => [Package['python-pip'], Package['python-setuptools'], Package['python-dev'], Package['build-essential']],
}
