gfal2-util
==========
GFAL 2 utils are a group of command line tools for file manipulations with any protocol managed by gfal2

## Installation
```bash
yum install gfal2-util gfal2-all
```

Mind that the protocol support of gfal2-util depends on the set of plugins installed in your machine.
Installing gfal2-all will trigger an installation of the plugins for file, SRM, GridFTP, HTTP/DAV, LFC, RFIO and DCAP.
If you need XROOTD support, you will need to install additionally gfal2-plugin-xrootd.

## List of commands
We provide here a brief overview of the command line tools we provide as part of this package.
To see detailed usage of each one, you can invoke them with --help to show all the possible options.

### Standard commands

#### gfal-bringonline
Perform a staging operation on the given SURL.

#### gfal-archivepoll
Perform an archive polling operation on a given SURL.

#### gfal-cat
Equivalent to cat. Print into the standard output the content of the requested file

#### gfal-chmod
Equivalent to chmod. Changes the access permissions of the requested file

#### gfal-copy
Equivalent to cp but more powerful. Copy a file, or set of files, between different
storages and/or local. Recursive mode is supported. Try --dry-run to validate what will happen.

#### gfal-evict
Requests a Tape storage to release the given file's disk replica.   
- For SRM storage, this is the equivalent of an unpin operation. The file is marked
as eligible for garbage collection 
- For CTA storage, this is the equivalent of an evict operation. The file's evict
counter is decreased. When the counter reaches zero, the file's disk replica 
is deleted immediately

#### gfal-ls
Equivalent to ls. List the content of a directory. Use -l to generate a detailed list.

#### gfal-mkdir
Equivalent to mkdir. Create a directory

#### gfal-rename
Equivalent to rename command. Moves the file from one location to another one
within the same storage

#### gfal-rm
Equivalent to rm. Remove a file, or a directory if -r is specified.
Try --dry-run if you want to validate what will happen without doing anything.

#### gfal-save
Reads from stdin and writes into a local or remote file.

#### gfal-stat
Equivalent to stat. Print information about the file or directory.

#### gfal-sum
Query or calculate the checksum of the given file.
Normally recognised checksums are adler32, md5 and sha1, but it depends on the protocol and/or storage software.

#### gfal-token
Requests a Storage Endpoint (SE) to issue a token for the given SURL (SE-issued token).
The token should be considered opaque, but most often used Grid implementations 
are JWTs or macaroons. These tokens have great applicability in HTTP-TPC as
they avoid the need to perform proxy certificate delegation.

#### gfal-xattr
Equivalent to attr. Query or set an extended attribute from a file or directory.
Which extended attributes are supported depend on the protocol. For instance user.replicas or user.comment can be used for SRM or LFC.

### Legacy commands
This commands exists purely to provide ways to access functionality previously provided by lcg-util.
We recommend avoiding the usage of these tools if possible.

#### gfal-legacy-register
Register a new replica in a catalog. We recommend using instead
```bash
gfal-xattr [surl] user.replicas=+new_replica
```

#### gfal-legacy-replicas
List replicas from a catalog or SRM. We recommend using instead
```bash
gfal-xattr [surl] user.replicas
```

#### gfal-legacy-unregister
Remove an existing replica from a catalog. We recommend using instead
```bash
gfal-xattr [surl] user.replicas=-replica
```

## License
This software is licensed under the [Apache 2 License](http://www.apache.org/licenses/LICENSE-2.0.html)

Copyright (c) 2013-2022 CERN  
Copyright (c) 2012-2013 Members of the EMI Collaboration  
    See http://www.eu-emi.eu/partners for details on the copyright holders.

## Contact
You can notify bugs or ask for feature requests via dmc-support@cern.ch or dmc-devel@cern.ch
