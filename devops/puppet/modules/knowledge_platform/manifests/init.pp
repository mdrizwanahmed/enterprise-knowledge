class knowledge_platform {
  file { '/tmp/knowledge-platform-managed.txt':
    ensure  => file,
    content => "Managed by Puppet module: knowledge_platform\n",
    mode    => '0644',
  }
}
