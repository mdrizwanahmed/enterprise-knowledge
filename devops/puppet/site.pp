file { '/tmp/knowledge-platform-status.txt':
  ensure  => file,
  content => "Enterprise Knowledge Intelligence Platform is managed by Puppet.\n",
  mode    => '0644',
}
