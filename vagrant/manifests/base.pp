
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
    name    => 'mongodb',
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
class pip {
    Exec {
        path        => $::path,
        require     => [Package['python-pip'], Package['python-setuptools'], Package['python-dev'], Package['build-essential'], Service['mongodb']],
        timeout     => 0, # Turn off the timeout stuff. It might take longer than 5 minutes.
        tries       => 5, # Try really hard to install all the pip packages.
        logoutput   => 'true',
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
