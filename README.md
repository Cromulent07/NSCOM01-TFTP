<div style="text-align: justify">

# Trivial File Transfer Protocol (TFTP)
## Background
Trivial File Transfer Protocol (TFTP) is a UDP-based application layer protocol that is used to perform a simple file upload or download within a LAN setting. At present, it is commonly used to transfer network appliance operating system images and configuration files to and from a computer for backup or update purposes. Since it is UDP-based, the TFTP specification includes mechanisms that allow applications to perform simplified reliable and ordered data delivery that would have otherwise been unavailable from the transport layer. The majority of TFTP applications conform to TFTP version2 , which has its specifications documented in RFC 1350 and later extended with additional features using RFCs 2347, 2348 and 2349.

## Objectives
This project is formulated as a supplement to classroom instruction for students to demonstrate the following:
- Review and comprehend the detailed function and design of network protocols as described in Internet standards documents
- Implement a working network application that conforms to Internet standards.

## Requirements

The client program may be implemented using either C, Java or Python sockets and must feature the following:

- Command line-based user interface only (No need to develop GUI).
- The client will specify (input) the server IP address.
- Support for both upload and download of binary files.
- When uploading:
    - The program can send any file on the computer to the TFTP server as long as the file is accessible to the user using its OS privileges
- When downloading:
    - The program must allow the client to provide the filename to use when saving the downloaded file to its machine
- Proper error handling which at the minimum should include the following:
    - Timeout for unresponsive server
    - Handling of duplicate ACK
    - User prompt for file not found, access violation, and disk full errors
    - You are responsible for proving these error-handling functions through test cases.

Support for option negotiation will merit additional points if correctly implemented

- Option to specify transfer block size (blksize)
- Communicate transfer size to server when uploading (tsize)
</div>