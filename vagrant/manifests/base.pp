
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
    'vim',
    ]:
    ensure   => 'latest',
    provider => 'aptitude';
}

# Stop the mongod service, SimpleMMO starts its own.
service { 'mongodb':
    name    => 'mongodb',
    enable  => 'false',
    ensure  => 'stopped',
    require => Package['mongodb'],
}

# Pull down the source
exec { 'git clone git://github.com/cnelsonsic/SimpleMMO.git':
    cwd     => '/home/vagrant',
    path    => $::path,
    creates => '/home/vagrant/SimpleMMO/.git/',
    refresh => 'git reset --hard HEAD; git pull',
    unless  => 'test `git pull`',
    require => Package['git'],
}

# Install the requirements.
class pip-packages {
    Package { provider => "pip" }
    package {
        'Elixir':
            ensure => '0.7.1';
        'sentry':
            ensure => '4.2.5';
        'raven':
            ensure => '1.7.6';
        'mock':
            ensure => '0.8.0';
        'pymongo':
            ensure => '2.1.1';
        'mongoengine':
            ensure => '0.6.9';
        'pymunk':
            ensure => '2.1.0';
        'requests':
            ensure => '0.12.1';
        'supervisor':
            ensure => '3.0a12';
        'supervisor_twiddler':
            ensure => '0.4';
        'tornado':
            ensure => '2.2.1';
    }
}
include pip-packages

# Compile a fresh libtcod
class libtcod {
    Package { provider => "aptitude" }
    package {[
        'mercurial',
        'electric-fence',
        'cmake',
        'libgl1-mesa-dev',
        'libpng-dev',
        'libsdl-dev',
        'upx-ucl',
        ]:
        ensure => 'latest';
    }

    exec { 'clone libtcod':
        command     => 'hg clone https://bitbucket.org/jice/libtcod',
        path        => $::path,
        cwd         => '/home/vagrant/',
        user        => 'vagrant',
        creates     => '/home/vagrant/libtcod/.hg',
        require     => Package['mercurial'],
    }

    exec { 'generate libtcod makefile':
        command     => 'bash ./generate-make.sh unix',
        path        => $::path,
        cwd         => '/home/vagrant/libtcod/cmake/',
        user        => 'vagrant',
        creates     => '/home/vagrant/libtcod/cmake/release/Makefile',
        require     => [Package['electric-fence'], Exec['clone libtcod'], Package['cmake']],
    }

    exec { 'build libtcod':
        command     => 'make',
        path        => $::path,
        cwd         => '/home/vagrant/libtcod/cmake/release',
        user        => 'vagrant',
        require     => [Exec['generate libtcod makefile']],
    }

    exec { 'install libtcod':
        command     => 'make install',
        path        => $::path,
        cwd         => '/home/vagrant/libtcod/cmake/release/',
        user        => 'vagrant',
        require     => [Exec['build libtcod'],],
    }
}
include libtcod

# Make sure mongodb has a folder
file { '/home/vagrant/SimpleMMO/mongodb':
    ensure  => 'directory',
    owner   => 'vagrant',
}

file { '/home/vagrant/SimpleMMO':
    recurse => 'true',
    owner   => 'vagrant',
    group   => 'vagrant',
    mode    => 700,
    require => Exec['git clone git://github.com/cnelsonsic/SimpleMMO.git'],
}

# TODO: Copy over sentry's config.
exec { 'sentry init':
    command     => 'sentry init /home/vagrant/.sentry/sentry.conf.py',
    path        => $::path,
    cwd         => '/home/vagrant/',
    user        => 'vagrant',
    creates     => '/home/vagrant/.sentry/sentry.conf.py',
    require     => Package['sentry'],
}

# Upgrade sentry's database before starting
exec {'sentry --config=sentry.conf.py upgrade':
    path    => $::path,
    cwd     => '/home/vagrant/SimpleMMO',
    user    => 'vagrant',
    tries   => 5, # Stupid thing tries to ask questions, but it gives up when you run it again.
    require => [Package['sentry'], Exec['sentry init']],
    before => Exec['supervisord'],
}

# Start up all the servers.
exec {'supervisord':
    cwd         => '/home/vagrant/SimpleMMO',
    path        => $::path,
    user        => 'vagrant',
    refresh     => 'supervisorctl reload',
    creates     => '/tmp/supervisor.sock',
    require     => [Package['mongodb'], File['/home/vagrant/SimpleMMO/mongodb']],
}
