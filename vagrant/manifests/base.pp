
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
    ensure => 'latest';
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
    logoutput => true,
    refresh => 'git reset --hard HEAD; git pull',
    unless  => 'test `git pull`',
    require => Package['git'],
}

# Install the requirements.
class pip {
    Exec {
        path        => $::path,
        require     => [Package['python-pip'], Package['python-setuptools'], Package['python-dev'], Package['build-essential'], Service['mongodb']],
        timeout     => 0, # Turn off the timeout stuff. It might take longer than 5 minutes.
        tries       => 5, # Try really hard to install all the pip packages.
    }
    exec {
        'pip install --use-mirrors Elixir==0.7.1':;
        'pip install --use-mirrors sentry==4.2.5':;
        'pip install --use-mirrors raven==1.7.6':;
        'pip install --use-mirrors mock==0.8':;
        'pip install --use-mirrors pymongo==2.1.1':;
        'pip install --use-mirrors mongoengine==0.6.9':;
        'pip install --use-mirrors pymunk==2.1.0':;
        'pip install --use-mirrors requests==0.12.1':;
        'pip install --use-mirrors supervisor==3.0a12':;
        'pip install --use-mirrors supervisor_twiddler==0.4':;
        'pip install --use-mirrors tornado==2.2.1':;
    }
}
include pip

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
exec {'sentry init /home/vagrant/.sentry/sentry.conf.py':
    path        => $::path,
    cwd         => '/home/vagrant/',
    user        => 'vagrant',
    creates     => '/home/vagrant/.sentry/sentry.conf.py',
    logoutput   => 'true',
    require     => Exec['pip install --use-mirrors sentry==4.2.5'],
}

# Upgrade sentry's database before starting
exec {'sentry --config=sentry.conf.py upgrade':
    path    => $::path,
    cwd     => '/home/vagrant/SimpleMMO',
    user    => 'vagrant',
    tries   => 5, # Stupid thing tries to ask questions, but it gives up when you run it again.
    logoutput => 'true',
    require => [Exec['pip install --use-mirrors sentry==4.2.5'], Exec['sentry init /home/vagrant/.sentry/sentry.conf.py']],
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
