#!/usr/bin/python

# Copyright (c) 2026 mschfh
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
---
module: diskutil
short_description: Manage disks and volumes on macOS
description:
  - This module manages disks and volumes on macOS hosts by using the C(diskutil) command.
  - Use O(info_type) to query disks, a device, APFS containers, APFS volume groups and file systems. These
    queries never modify anything and do not require root privileges.
  - Use O(state) to idempotently change the mount state of a disk or a volume, the presence of an APFS volume,
    the ownership of a volume, or to erase a disk or a volume. All state changes require root privileges.
author:
  - mschfh (@mschfh)
version_added: 13.5.0
requirements:
  - macOS
  - Root privileges to change the state of a disk or a volume
extends_documentation_fragment:
  - community.general._attributes
  - community.general._attributes.platform
attributes:
  check_mode:
    support: full
  diff_mode:
    support: partial
  platform:
    platforms: macos
options:
  state:
    description:
      - The desired state of the target disk or volume.
      - With V(present) and V(absent), the APFS volume named O(volume_name) inside the APFS container
        O(container) is created or removed. Instead of O(container), O(device) can be used to refer to a
        volume that already exists. In this case the volume is renamed to O(volume_name) instead.
      - With V(mounted) and V(unmounted), the volume is mounted or unmounted. If O(mount_point) is set while
        the volume is mounted somewhere else, the volume is unmounted first and then mounted at O(mount_point).
      - With V(ejected), all mounted volumes of the whole disk O(device) are unmounted, and the disk is ejected.
      - With V(owned) and V(unowned), ownership on the volume O(device) is enabled or disabled.
      - With V(erased), the disk or the volume is erased and re-created with the file system and the name given
        in O(filesystem) and O(volume_name). Erasing is irreversible, and therefore requires O(erase_confirm) to
        be enabled.
      - Mutually exclusive with O(info_type).
    type: str
    choices: [present, absent, mounted, unmounted, ejected, owned, unowned, erased]
  info_type:
    description:
      - The kind of information to query. Nothing is modified when this option is used.
      - V(disks) queries all disks together with their partitions and the volumes of their APFS containers.
      - V(device) queries all information about O(device).
      - V(apfs) queries all APFS containers together with their volumes.
      - V(volume_groups) queries all APFS volume groups.
      - V(filesystems) queries all file systems that can be used for erasing and partitioning.
      - Mutually exclusive with O(state).
    type: str
    choices: [disks, device, apfs, volume_groups, filesystems]
  device:
    description:
      - The device to operate on.
      - Can be a device identifier like V(disk2) or V(disk2s1), a device node like V(/dev/disk2), a volume
        name, or a volume UUID. Device nodes are converted to device identifiers before they are passed to
        C(diskutil).
      - Required for O(info_type=device), and for the V(mounted), V(unmounted), V(ejected), V(owned),
        V(unowned) and V(erased) states.
    type: str
  container:
    description:
      - The APFS container to add the APFS volume to, or to remove the APFS volume from.
      - This is the APFS container reference as reported by C(diskutil apfs list), for example V(disk2s1) on
        older versions of macOS, or V(disk2) for a container that is its own synthesized disk.
    type: str
  volume_name:
    description:
      - The name of the APFS volume.
      - Required for the V(present) state. For V(absent) and V(erased) it is optional, and is then used to
        identify a volume inside O(container), or as the name of the newly created volume.
    type: str
  mount_point:
    description:
      - The path at which the volume should be mounted.
      - Only considered for the V(mounted) state.
    type: path
  force:
    description:
      - Whether to unmount or eject even when the volume is busy.
    type: bool
    default: false
  filesystem:
    description:
      - The file system to use for a new APFS volume, or the file system to erase a disk or a volume with.
      - See the possible values by querying O(info_type=filesystems) on the target host.
    type: str
    default: APFS
  quota:
    description:
      - The maximum size of the APFS volume, for example V(10g). The APFS container decides how much space is
        available to all of its volumes.
    type: str
  reserve:
    description:
      - The minimum amount of space to reserve for other volumes of the APFS container, for example V(2g).
    type: str
  mount_new_volume:
    description:
      - Whether a newly created APFS volume should be mounted.
    type: bool
    default: true
  erase_scope:
    description:
      - Whether V(state=erased) should erase a whole disk including its partition map, or only one of its
        volumes.
    type: str
    choices: [volume, disk]
    default: volume
  partition_scheme:
    description:
      - The partition scheme to write when O(erase_scope=disk).
      - When not specified, C(diskutil) chooses a partition scheme appropriate for the machine.
      - The partition scheme is only written when erasing, it is not compared when deciding whether anything
        needs to be changed.
    type: str
    choices: [APM, MBR, GPT]
  erase_confirm:
    description:
      - Must be enabled to run V(state=erased). Erasing a disk or a volume permanently destroys all data on it.
    type: bool
    default: false
notes:
  - This module requires macOS. On other operating systems the C(diskutil) command does not exist, and the
    module fails early.
  - Only the read-only queries work without root privileges. Use C(become=true) for all state changes.
  - Erasing a disk or a volume with V(state=erased) cannot be undone. The module only performs the operation
    when O(erase_confirm) is enabled.
  - macOS 26 renamed several keys of the property lists that C(diskutil -plist) prints, and no longer has the
    C(mountinfo) verb. The module uses the new keys where they exist, and the old ones otherwise, so that it
    works with older versions of macOS as well.
"""

EXAMPLES = r"""
- name: List all disks and their partitions
  community.general.diskutil:
    info_type: disks
  register: disks

- name: List all APFS containers and their volumes
  community.general.diskutil:
    info_type: apfs
  register: containers

- name: List all file systems that can be used for erasing
  community.general.diskutil:
    info_type: filesystems

- name: Get all information about a volume
  community.general.diskutil:
    info_type: device
    device: /dev/disk2s1

- name: Mount a volume at /Volumes/data
  community.general.diskutil:
    state: mounted
    device: disk2s1
    mount_point: /Volumes/data
  become: true

- name: Unmount a volume even when it is busy
  community.general.diskutil:
    state: unmounted
    device: disk2s1
    force: true
  become: true

- name: Unmount and eject an external disk
  community.general.diskutil:
    state: ejected
    device: disk4
  become: true

- name: Create an APFS volume in a container
  community.general.diskutil:
    state: present
    container: disk2
    volume_name: Data
    quota: 100g
  become: true

- name: Rename an existing APFS volume
  community.general.diskutil:
    state: present
    device: disk2s2
    volume_name: Work
  become: true

- name: Remove an APFS volume from its container
  community.general.diskutil:
    state: absent
    container: disk2
    volume_name: Data
  become: true

- name: Enable ownership on a volume
  community.general.diskutil:
    state: owned
    device: disk2s1
  become: true

- name: Erase a volume and re-create it as APFS
  community.general.diskutil:
    state: erased
    device: disk2s1
    volume_name: Scratch
    filesystem: APFS
    erase_confirm: true
  become: true

- name: Erase a whole disk using a GPT partition scheme
  community.general.diskutil:
    state: erased
    device: disk4
    volume_name: Data
    filesystem: APFS
    erase_scope: disk
    partition_scheme: GPT
    erase_confirm: true
  become: true
"""

RETURN = r"""
before:
  description: The device information before the module made any changes.
  returned: when diff mode is active and O(device) is specified
  type: dict
  sample: {"DeviceIdentifier": "disk2s1", "MountPoint": "", "FilesystemName": "APFS"}
after:
  description: The device information after the module made any changes.
  returned: when diff mode is active and O(device) is specified
  type: dict
  sample: {"DeviceIdentifier": "disk2s1", "MountPoint": "/Volumes/data", "FilesystemName": "APFS"}
disks:
  description: The normalized disks together with their partitions and APFS volumes, when O(info_type=disks)
    is used.
  returned: when O(info_type=disks) is used
  type: list
  elements: dict
  sample: [{"device_identifier": "disk0", "size": 500107862016, "partitions": []}]
whole_disks:
  description: The device identifiers of all whole disks, when O(info_type=disks) is used.
  returned: when O(info_type=disks) is used
  type: list
  elements: str
  sample: ["disk0", "disk2"]
partitions:
  description: The normalized partitions of all disks, when O(info_type=disks) is used.
  returned: when O(info_type=disks) is used
  type: list
  elements: dict
  sample: [{"device_identifier": "disk2s1", "name": "untitled", "filesystem": "APFS", "mounted": true}]
containers:
  description: The normalized APFS containers together with their volumes, when O(info_type=apfs) is used.
  returned: when O(info_type=apfs) is used
  type: list
  elements: dict
  sample: [{"reference": "disk2", "capacity": 500107862016, "volumes": []}]
volume_groups:
  description: The normalized APFS volume groups, when O(info_type=volume_groups) is used.
  returned: when O(info_type=volume_groups) is used
  type: list
  elements: dict
  sample: []
filesystems:
  description: The file systems that can be used for erasing and partitioning, when O(info_type=filesystems)
    is used.
  returned: when O(info_type=filesystems) is used
  type: list
  elements: str
  sample: ["APFS", "ExFAT", "MS-DOS", "HFS+", "Case-sensitive APFS", "Journaled HFS+"]
info:
  description: The raw, normalized output of C(diskutil info -plist) for O(device).
  returned: when O(info_type=device) is used, or when a state change queried the device
  type: dict
  sample: {"DeviceIdentifier": "disk2s1", "VolumeName": "data", "MountPoint": "/Volumes/data"}
volume_device:
  description: The device identifier of the APFS volume that was created, renamed or removed.
  returned: on success, when the V(present) or V(absent) state is used and a volume was found or affected
  type: str
  sample: disk2s2
device:
  description: The resolved device identifier of the device that was queried or changed.
  returned: when device information could be queried
  type: str
  sample: disk2s1
device_node:
  description: The resolved device node of the device that was queried or changed.
  returned: when device information could be queried
  type: str
  sample: /dev/disk2s1
parent_whole_disk:
  description: The whole disk the queried device belongs to.
  returned: when device information could be queried
  type: str
  sample: disk2
whole_disk:
  description: Whether the queried device is a whole disk.
  returned: when device information could be queried
  type: bool
  sample: false
volume_name:
  description: The name of the queried volume.
  returned: when device information could be queried
  type: str
  sample: data
volume_uuid:
  description: The UUID of the queried volume.
  returned: when device information could be queried
  type: str
  sample: 8A9F1D5E-6C8B-4A0D-9B4E-7C1D0F2A5E31
volume_is_mounted:
  description: Whether the queried volume is currently mounted.
  returned: when device information could be queried
  type: bool
  sample: true
mount_point:
  description: The mount point of the queried volume.
  returned: when device information could be queried
  type: str
  sample: /Volumes/data
filesystem:
  description: The file system of the queried volume, in the spelling that C(diskutil) expects.
  returned: when device information could be queried
  type: str
  sample: APFS
filesystem_type:
  description: The file system type of the queried volume, as reported by C(diskutil).
  returned: when device information could be queried
  type: str
  sample: apfs
content:
  description: The content type of the queried device, for example V(Apple_APFS).
  returned: when device information could be queried
  type: str
  sample: Apple_APFS
size:
  description: The size of the queried device in bytes.
  returned: when device information could be queried
  type: int
  sample: 500107862016
volume_size:
  description: The size of the queried volume in bytes.
  returned: when device information could be queried
  type: int
  sample: 499963174912
free_space:
  description: The free space of the queried volume in bytes.
  returned: when device information could be queried
  type: int
  sample: 123456789012
block_size:
  description: The block size of the queried device in bytes.
  returned: when device information could be queried
  type: int
  sample: 4096
internal:
  description: Whether the queried device is internal to the machine.
  returned: when device information could be queried
  type: bool
  sample: true
ejectable:
  description: Whether the queried device can be ejected.
  returned: when device information could be queried
  type: bool
  sample: false
removable_media:
  description: Whether the queried device is removable media.
  returned: when device information could be queried
  type: bool
  sample: false
solid_state:
  description: Whether the queried device is a solid state device.
  returned: when device information could be queried
  type: bool
  sample: true
writable:
  description: Whether the queried device is writable.
  returned: when device information could be queried
  type: bool
  sample: true
read_only:
  description: Whether the queried device is read-only.
  returned: when device information could be queried
  type: bool
  sample: false
encrypted:
  description: Whether the queried volume is encrypted.
  returned: when device information could be queried
  type: bool
  sample: false
media_name:
  description: The media name of the queried device.
  returned: when device information could be queried
  type: str
  sample: APPLE SSD AP0256Z
media_type:
  description: The media type of the queried device, for example V(NVM).
  returned: when device information could be queried
  type: str
  sample: NVM
protocol:
  description: The bus protocol of the queried device, for example V(NVMe).
  returned: when device information could be queried
  type: str
  sample: NVMe
smart_status:
  description: The SMART status of the queried device.
  returned: when device information could be queried
  type: str
  sample: Verified
owners:
  description: The ownership states of the queried volume, if C(diskutil) reports them.
  returned: when device information could be queried
  type: list
  elements: str
  sample: ["Enabled"]
ownership_disabled:
  description: Whether ownership is disabled on the queried volume.
  returned: when device information could be queried
  type: bool
  sample: false
ownership_supported:
  description: Whether ownership can be disabled on the queried volume.
  returned: when device information could be queried
  type: bool
  sample: true
container_reference:
  description: The APFS container the queried volume belongs to.
  returned: when device information could be queried
  type: str
  sample: disk2
apfs_group:
  description: The APFS volume group the queried volume belongs to.
  returned: when device information could be queried
  type: str
  sample: 4A2C9D18-1E8B-4A5F-9C33-6B7D8E9F0A12
apfs_role:
  description: The APFS role of the queried volume, for example V(Data).
  returned: when device information could be queried
  type: str
  sample: Data
"""

import datetime
import plistlib

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_bytes

MOUNT_STATES = ("mounted", "unmounted")
OWNERSHIP_STATES = ("owned", "unowned")
# The header of the second column of the table that `diskutil listFilesystems` prints. Its position
# tells where the file system personalities end. Used as a fallback if the header is missing.
FILESYSTEMS_HEADER = "USER VISIBLE NAME"
FILESYSTEMS_COLUMN = 32


def as_bool(value):
    """Interprets a value coming from a property list as a boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("yes", "true", "1", "on")
    return False


def first(mapping, *keys, default=None):
    """Returns the value of the first of the given keys that is present in the mapping."""
    for key in keys:
        if key in mapping:
            return mapping[key]
    return default


def device_id(device):
    """Returns the device identifier of a device node like ``/dev/disk2s1``."""
    if not device:
        return None
    if device.startswith("/dev/"):
        return device[len("/dev/") :]
    return device


def device_node(identifier):
    """Returns the device node of a device identifier like ``disk2s1``."""
    if not identifier:
        return None
    if identifier.startswith("/dev/"):
        return identifier
    return f"/dev/{identifier}"


def is_mounted(mapping):
    """Returns whether a volume is mounted.

    macOS 26 no longer reports a ``Mounted`` boolean, but an empty ``MountPoint`` instead.
    """
    if "Mounted" in mapping:
        return as_bool(mapping["Mounted"])
    return bool(mapping.get("MountPoint"))


def sanitize(value):
    """Converts the values of a property list into JSON-serializable values."""
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    return value


def normalize_partition(partition):
    """Normalizes one entry of a partition map, or of the APFS volumes of a container."""
    identifier = partition.get("DeviceIdentifier")
    return {
        "device_identifier": identifier,
        "device_node": partition.get("DeviceNode") or device_node(identifier),
        "name": partition.get("VolumeName"),
        "volume_uuid": partition.get("VolumeUUID") or partition.get("DiskUUID"),
        "content": partition.get("Content"),
        "filesystem": first(partition, "FileSystemPersonality", "FilesystemName"),
        "size": partition.get("Size"),
        "block_size": first(partition, "BlockSize", "DeviceBlockSize"),
        "mounted": is_mounted(partition),
        "mount_point": partition.get("MountPoint"),
        "writable": as_bool(partition.get("WritableVolume")),
        "read_only": as_bool(partition.get("ReadOnlyVolume")),
        "encrypted": as_bool(partition.get("VolumeEncryptionEnabled")),
        "container_reference": partition.get("APFSContainerReference"),
        "apfs_group": first(partition, "APFSVolumeGroup", "APFSVolumeGroupID"),
        "fusion_drive": partition.get("FusionDrive"),
    }


def normalize_volume(volume):
    """Normalizes one entry of the volumes of an APFS container."""
    identifier = first(volume, "DeviceIdentifier", "APFSVolumeDeviceIdentifier")
    roles = volume.get("Roles")
    if roles is None:
        role = volume.get("APFSVolumeRole")
        roles = [role] if role else []
    return {
        "device_identifier": identifier,
        "name": first(volume, "Name", "APFSVolumeName"),
        "uuid": volume.get("APFSVolumeUUID"),
        "size": first(volume, "Size", "APFSVolumeCapacity"),
        "capacity_in_use": volume.get("CapacityInUse"),
        "capacity_free": volume.get("APFSVolumeCapacityFree"),
        "capacity_quota": volume.get("CapacityQuota"),
        "capacity_reserve": volume.get("CapacityReserve"),
        "roles": list(roles),
        "encrypted": as_bool(first(volume, "Encryption", "APFSVolumeIsEncrypted")),
        "filevault": as_bool(first(volume, "FileVault", "APFSVolumeIsFileVault")),
        "locked": as_bool(volume.get("Locked")),
        "system": as_bool(volume.get("APFSVolumeIsSystem")) or "System" in roles,
        "recovery": as_bool(volume.get("APFSVolumeIsRecovery")) or "Recovery" in roles,
    }


def normalize_container(container):
    """Normalizes one entry of the APFS containers."""
    stores = first(container, "PhysicalStores", "APFSPhysicalStores") or []
    volumes = first(container, "Volumes", "APFSContainerVolumes") or []
    return {
        "reference": first(container, "ContainerReference", "APFSContainerReference"),
        "uuid": container.get("APFSContainerUUID"),
        "capacity": first(container, "CapacityCeiling", "APFSContainerCapacity"),
        "capacity_free": first(container, "CapacityFree", "APFSContainerCapacityFree"),
        "physical_stores": [device_id(first(store, "APFSPhysicalStore", "DeviceIdentifier")) for store in stores],
        "volumes": [normalize_volume(volume) for volume in volumes],
    }


def normalize_disk(disk, volumes=None):
    """Normalizes one whole disk, together with the volumes of its partitions."""
    identifier = disk.get("DeviceIdentifier")
    partitions = [normalize_partition(part) for part in (first(disk, "PartitionMaps", "Partitions") or [])]
    if volumes:
        partitions.extend(volumes)
    return {
        "device_identifier": identifier,
        "device_node": disk.get("DeviceNode") or device_node(identifier),
        "media_name": disk.get("MediaName"),
        "media_type": disk.get("MediaType"),
        "protocol": first(disk, "Protocol", "BusProtocol"),
        "internal": as_bool(first(disk, "Internal", "OSInternal")),
        "ejectable": as_bool(disk.get("Ejectable")),
        "removable_media": as_bool(disk.get("RemovableMedia")),
        "solid_state": as_bool(disk.get("SolidState")),
        "virtual_or_physical": disk.get("VirtualOrPhysical"),
        "content": disk.get("Content"),
        "size": first(disk, "Size", "IOKitSize"),
        "block_size": first(disk, "BlockSize", "DeviceBlockSize"),
        "smart_status": first(disk, "SmartStatus", "SMARTStatus"),
        "partitions": partitions,
    }


def parse_filesystems(output):
    """Parses the table that ``diskutil listFilesystems`` prints.

    The personalities are in the first column of the table, which has a fixed width. Aliases and the
    user visible names are listed on indented continuation lines, which are ignored.
    """
    lines = output.splitlines()
    # The last line of dashes separates the introduction from the table itself.
    separators = [i for i, line in enumerate(lines) if line.strip() and set(line.strip()) == {"-"}]
    if separators:
        lines = lines[separators[-1] + 1 :]
    column = FILESYSTEMS_COLUMN
    for line in lines:
        index = line.find(FILESYSTEMS_HEADER)
        if index > 0:
            column = index
            break
    personalities = []
    for line in lines:
        if not line.strip() or line[:1].isspace():
            continue
        personality = line[:column].rstrip()
        if not personality or personality == "PERSONALITY":
            continue
        personalities.append(personality)
    return personalities


class DiskUtil:
    """Wraps the ``diskutil`` command."""

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.diskutil = module.get_bin_path("diskutil", required=True)
        self.result = {"changed": False}

    # -- running commands ----------------------------------------------------------

    def run(self, args, allow_failure=False):
        """Runs a ``diskutil`` command, and fails the module if it did not succeed."""
        rc, out, err = self.module.run_command([self.diskutil] + args, check_rc=False)
        if rc != 0 and not allow_failure:
            detail = err.strip() or out.strip() or f"exit status {rc}"
            self.module.fail_json(
                msg=f"Failed to run 'diskutil {args[0]}': {detail}",
                rc=rc,
                stdout=out,
                stderr=err,
            )
        return rc, out, err

    def parse_plist(self, out, args, err, allow_failure=False):
        """Parses the output of a ``diskutil`` command that was called with ``-plist``."""
        try:
            return sanitize(plistlib.loads(to_bytes(out)))
        except Exception as exc:
            if allow_failure:
                return None
            self.module.fail_json(
                msg=f"Failed to parse the output of 'diskutil {' '.join(args)} -plist': {exc}",
                stdout=out,
                stderr=err,
            )

    def plist(self, args, allow_failure=False):
        """Runs a ``diskutil`` command with ``-plist``, and returns the parsed property list."""
        rc, out, err = self.run(args + ["-plist"], allow_failure=allow_failure)
        if rc != 0:
            return None
        return self.parse_plist(out, args, err, allow_failure)

    def info(self, device, allow_failure=False):
        """Returns the parsed output of ``diskutil info -plist`` for a device.

        Unlike the other verbs, C(diskutil info) expects the C(-plist) flag before the device.
        """
        identifier = device_id(device)
        rc, out, err = self.run(["info", "-plist", identifier], allow_failure=allow_failure)
        if rc != 0:
            return None
        return self.parse_plist(out, ["info", identifier], err, allow_failure)

    def disks(self):
        """Returns the parsed output of ``diskutil list -plist``."""
        return self.plist(["list"]) or {}

    def apfs_containers(self):
        """Returns the APFS containers as reported by ``diskutil apfs list -plist``."""
        apfs = self.plist(["apfs", "list"]) or {}
        return first(apfs, "Containers", "APFSContainers") or []

    def disk_entry(self, device, listing=None):
        """Returns the entry of ``diskutil list -plist`` for a whole disk, or C(None)."""
        listing = self.disks() if listing is None else listing
        identifier = device_id(device)
        for entry in listing.get("AllDisksAndPartitions") or []:
            if isinstance(entry, dict) and entry.get("DeviceIdentifier") == identifier:
                return entry
        for disk in listing.get("Disks") or []:
            if disk.get("DeviceIdentifier") == identifier or disk.get("DeviceNode") == device:
                return disk
        return None

    def mounted_volumes(self, whole_disk, listing=None):
        """Returns the identifiers of all mounted volumes that belong to a whole disk."""
        listing = self.disks() if listing is None else listing
        identifier = device_id(whole_disk)
        volumes = []

        def collect(parts):
            for part in parts or []:
                if is_mounted(part):
                    volumes.append(device_id(part.get("DeviceIdentifier")))

        stores = []
        for entry in listing.get("AllDisksAndPartitions") or []:
            if not isinstance(entry, dict):
                continue
            if entry.get("DeviceIdentifier") == identifier:
                collect(first(entry, "PartitionMaps", "Partitions"))
                for part in first(entry, "PartitionMaps", "Partitions") or []:
                    if part.get("Content") in ("Apple_APFS", "Apple_CoreStorage"):
                        stores.append(part.get("DeviceIdentifier"))
            else:
                stores_found = [
                    device_id(first(store, "APFSPhysicalStore", "DeviceIdentifier"))
                    for store in (entry.get("APFSPhysicalStores") or [])
                ]
                if stores_found and set(stores_found) & set(stores):
                    collect(entry.get("APFSVolumes"))
        return [volume for volume in volumes if volume]

    def find_volume(self, containers, device=None, container=None, name=None):
        """Searches an APFS volume in a list of containers as reported by ``diskutil apfs list -plist``."""
        identifier = device_id(device)
        for entry in containers:
            reference = first(entry, "ContainerReference", "APFSContainerReference")
            if container is not None and reference != device_id(container):
                continue
            for volume in first(entry, "Volumes", "APFSContainerVolumes") or []:
                if name is not None and first(volume, "Name", "APFSVolumeName") != name:
                    continue
                volume_device = first(volume, "DeviceIdentifier", "APFSVolumeDeviceIdentifier")
                if identifier is not None and volume_device != identifier:
                    continue
                return reference, volume
        return None, None

    # -- helpers --------------------------------------------------------------------

    def require(self, *names):
        """Fails the module unless all of the given options have been specified."""
        for name in names:
            if not self.params.get(name):
                self.module.fail_json(
                    msg=f"The '{name}' option is required for this operation",
                    state=self.params.get("state"),
                    info_type=self.params.get("info_type"),
                )

    def publish_info(self, info):
        """Copies the interesting values of ``diskutil info -plist`` into the result."""
        identifier = info.get("DeviceIdentifier")
        owners = info.get("Owners") or []
        self.result["info"] = info
        self.result["device"] = identifier
        self.result["device_node"] = info.get("DeviceNode") or device_node(identifier)
        self.result["parent_whole_disk"] = info.get("ParentWholeDisk")
        self.result["whole_disk"] = as_bool(info.get("WholeDisk"))
        self.result["volume_name"] = info.get("VolumeName")
        self.result["volume_uuid"] = first(info, "VolumeUUID", "DiskUUID")
        self.result["volume_is_mounted"] = is_mounted(info)
        self.result["mount_point"] = info.get("MountPoint") or None
        self.result["filesystem"] = first(info, "FileSystemPersonality", "FilesystemName")
        self.result["filesystem_type"] = info.get("FilesystemType")
        self.result["content"] = info.get("Content")
        self.result["size"] = first(info, "Size", "IOKitSize", "DiskSize")
        self.result["volume_size"] = info.get("VolumeSize")
        self.result["free_space"] = first(info, "FreeSpace", "VolumeFreeSpace")
        self.result["block_size"] = first(info, "DeviceBlockSize", "BlockSize")
        self.result["internal"] = as_bool(info.get("Internal"))
        self.result["ejectable"] = as_bool(info.get("Ejectable"))
        self.result["removable_media"] = as_bool(info.get("RemovableMedia"))
        self.result["solid_state"] = as_bool(info.get("SolidState"))
        self.result["media_name"] = info.get("MediaName")
        self.result["media_type"] = info.get("MediaType")
        self.result["protocol"] = first(info, "BusProtocol", "Protocol")
        self.result["smart_status"] = first(info, "SMARTStatus", "SmartStatus")
        self.result["writable"] = as_bool(first(info, "Writable", "WritableVolume"))
        self.result["read_only"] = as_bool(info.get("ReadOnlyVolume")) or (
            "Writable" in info and not as_bool(info["Writable"])
        )
        self.result["encrypted"] = as_bool(first(info, "Encryption", "VolumeEncryptionEnabled"))
        self.result["owners"] = owners
        self.result["ownership_disabled"] = (
            as_bool(info.get("OwnersDisabled"))
            or ("Disabled" in owners)
            or ("GlobalPermissionsEnabled" in info and not as_bool(info["GlobalPermissionsEnabled"]))
        )
        self.result["ownership_supported"] = as_bool(first(info, "SupportsGlobalPermissionsDisable", default=True))
        self.result["container_reference"] = first(info, "APFSContainerReference", "ContainerReference")
        self.result["apfs_group"] = first(info, "APFSVolumeGroup", "APFSVolumeGroupID")
        self.result["apfs_role"] = first(info, "APFSVolumeRole", "Role")

    def unmount(self, device, force=False):
        """Unmounts a volume."""
        args = ["unmount"]
        if force:
            args.append("-force")
        args.append(device_id(device))
        self.run(args)

    # -- read-only queries ---------------------------------------------------------

    def do_disks(self):
        listing = self.disks()
        containers = {}
        for entry in listing.get("AllDisksAndPartitions") or []:
            if not isinstance(entry, dict):
                continue
            for store in entry.get("APFSPhysicalStores") or []:
                store_id = device_id(first(store, "APFSPhysicalStore", "DeviceIdentifier"))
                containers.setdefault(store_id, []).extend(
                    normalize_partition(volume) for volume in (entry.get("APFSVolumes") or [])
                )
        source = listing.get("Disks") or listing.get("AllDisksAndPartitions") or []
        disks = []
        for entry in source:
            if not isinstance(entry, dict):
                continue
            volumes = []
            for part in first(entry, "PartitionMaps", "Partitions") or []:
                volumes.extend(containers.get(part.get("DeviceIdentifier")) or [])
            disks.append(normalize_disk(entry, volumes))
        self.result["disks"] = disks
        self.result["whole_disks"] = listing.get("WholeDisks") or []
        self.result["partitions"] = [part for disk in disks for part in disk["partitions"]]

    def do_info(self):
        """Runs the read-only query the user asked for."""
        info_type = self.params["info_type"]
        if info_type == "disks":
            self.do_disks()
        elif info_type == "device":
            self.require("device")
            self.publish_info(self.info(self.params["device"]))
        elif info_type == "apfs":
            self.result["containers"] = [normalize_container(entry) for entry in self.apfs_containers()]
        elif info_type == "volume_groups":
            self.do_volume_groups()
        elif info_type == "filesystems":
            dummy_rc, out, dummy_err = self.run(["listFilesystems"])
            self.result["filesystems"] = parse_filesystems(out)

    def do_volume_groups(self):
        apfs = self.plist(["apfs", "listVolumeGroups"]) or {}
        groups = apfs.get("APFSVolumeGroups")
        if groups is None:
            groups = [
                group
                for container in first(apfs, "Containers", "APFSContainers") or []
                for group in (container.get("VolumeGroups") or [])
            ]
        self.result["volume_groups"] = [
            {
                "uuid": group.get("APFSVolumeGroupUUID"),
                "volumes": [
                    {
                        "device_identifier": volume.get("DeviceIdentifier"),
                        "role": volume.get("Role"),
                        "no_browse_role": as_bool(volume.get("NoBrowseRole")),
                    }
                    for volume in (group.get("Volumes") or [])
                ],
            }
            for group in groups or []
        ]

    # -- APFS volumes --------------------------------------------------------------

    def add_volume(self, container):
        """Creates a new APFS volume, and returns its device identifier."""
        args = ["apfs", "addVolume", device_id(container), self.params["filesystem"], self.params["volume_name"]]
        if self.params["quota"]:
            args.extend(["-quota", self.params["quota"]])
        if self.params["reserve"]:
            args.extend(["-reserve", self.params["reserve"]])
        if not self.params["mount_new_volume"]:
            args.append("-nomount")
        elif self.params["mount_point"]:
            args.extend(["-mountpoint", self.params["mount_point"]])
        self.run(args)
        dummy_ref, volume = self.find_volume(
            self.apfs_containers(), container=container, name=self.params["volume_name"]
        )
        return first(volume, "DeviceIdentifier", "APFSVolumeDeviceIdentifier") if volume else None

    def state_present(self):
        if self.params["device"] and not self.params["volume_name"]:
            self.module.fail_json(
                msg="The 'volume_name' option is required when 'device' is used together with state=present, "
                "because the volume is renamed to it",
            )
        self.require("volume_name")
        if not self.params["device"]:
            self.require("container")
        containers = self.apfs_containers()

        if self.params["device"]:
            reference, volume = self.find_volume(containers, device=self.params["device"])
            if volume is not None:
                self.result["volume_device"] = device_id(
                    first(volume, "DeviceIdentifier", "APFSVolumeDeviceIdentifier")
                )
                if first(volume, "Name", "APFSVolumeName") == self.params["volume_name"]:
                    return
                if self.params["container"] and reference != device_id(self.params["container"]):
                    self.module.fail_json(
                        msg=f"Device '{self.params['device']}' belongs to the APFS container '{reference}', "
                        f"and not to '{self.params['container']}'",
                    )
                self.result["changed"] = True
                if self.module.check_mode:
                    return
                self.run(["rename", device_id(self.params["device"]), self.params["volume_name"]])
                return
            if not self.params["container"]:
                self.module.fail_json(
                    msg=f"There is no APFS volume called '{self.params['device']}', therefore the 'container' "
                    f"option is required to create a volume called '{self.params['volume_name']}'",
                )

        dummy_ref, volume = self.find_volume(
            containers, container=self.params["container"], name=self.params["volume_name"]
        )
        if volume is not None:
            self.result["volume_device"] = device_id(first(volume, "DeviceIdentifier", "APFSVolumeDeviceIdentifier"))
            return
        self.result["changed"] = True
        if self.module.check_mode:
            return
        self.result["volume_device"] = self.add_volume(self.params["container"])

    def state_absent(self):
        if not self.params["device"] and not (self.params["container"] and self.params["volume_name"]):
            self.module.fail_json(
                msg="Either the 'device' option, or both the 'container' and the 'volume_name' options are "
                "required when state=absent",
            )
        dummy_ref, volume = self.find_volume(
            self.apfs_containers(),
            device=self.params["device"],
            container=self.params["container"],
            name=self.params["volume_name"],
        )
        if volume is None:
            return
        self.result["volume_device"] = device_id(first(volume, "DeviceIdentifier", "APFSVolumeDeviceIdentifier"))
        self.result["changed"] = True
        if self.module.check_mode:
            return
        self.run(["apfs", "deleteVolume", self.result["volume_device"]])

    # -- mount state ---------------------------------------------------------------

    def state_mounted(self):
        self.publish_info(self.info(self.params["device"]))
        mounted = self.result["volume_is_mounted"]
        wanted = self.params["mount_point"]
        if mounted and (not wanted or wanted == self.result["mount_point"]):
            return
        self.result["changed"] = True
        if self.module.check_mode:
            return
        if mounted:
            self.unmount(self.params["device"], force=self.params["force"])
        args = ["mount"]
        if wanted:
            args.extend(["-mountPoint", wanted])
        args.append(device_id(self.params["device"]))
        self.run(args)

    def state_unmounted(self):
        self.publish_info(self.info(self.params["device"]))
        if not self.result["volume_is_mounted"]:
            return
        self.result["changed"] = True
        if self.module.check_mode:
            return
        self.unmount(self.params["device"], force=self.params["force"])

    def state_ejected(self):
        listing = self.disks()
        if self.disk_entry(self.params["device"], listing) is None:
            # The disk is not in the partition table anymore, so there is nothing left to eject.
            return
        mounted = self.mounted_volumes(self.params["device"], listing)
        if not mounted:
            return
        self.result["changed"] = True
        if self.module.check_mode:
            return
        for volume in mounted:
            self.unmount(volume, force=self.params["force"])
        args = ["eject"]
        if self.params["force"]:
            args.append("-force")
        args.append(device_id(self.params["device"]))
        self.run(args)

    # -- ownership -----------------------------------------------------------------

    def state_ownership(self):
        self.publish_info(self.info(self.params["device"]))
        if not self.result["ownership_supported"]:
            self.module.fail_json(
                msg=f"Ownership cannot be disabled on the volume '{self.params['device']}' on this system",
            )
        enabled = not self.result["ownership_disabled"]
        if enabled == (self.params["state"] == "owned"):
            return
        self.result["changed"] = True
        if self.module.check_mode:
            return
        self.run(["enableOwnership" if not enabled else "disableOwnership", device_id(self.params["device"])])

    # -- erase ---------------------------------------------------------------------

    def disk_already_erased(self, name):
        """Returns whether a whole disk consists of the requested volume, and nothing else."""
        listing = self.disks()
        disk = self.disk_entry(self.params["device"], listing)
        if disk is None:
            return True
        stores = [
            part.get("DeviceIdentifier")
            for part in (first(disk, "PartitionMaps", "Partitions") or [])
            if part.get("Content") != "EFI"
        ]
        if len(stores) != 1:
            return False
        for entry in listing.get("AllDisksAndPartitions") or []:
            if not isinstance(entry, dict):
                continue
            found = [
                device_id(first(store, "APFSPhysicalStore", "DeviceIdentifier"))
                for store in (entry.get("APFSPhysicalStores") or [])
            ]
            if stores[0] in found:
                volumes = entry.get("APFSVolumes") or []
                return len(volumes) == 1 and volumes[0].get("VolumeName") == name
        return False

    def state_erased(self):
        if not self.params["erase_confirm"]:
            self.module.fail_json(
                msg="Erasing a disk or a volume cannot be undone, therefore the 'erase_confirm' option must be "
                "enabled to run state=erased",
            )
        name = self.params["volume_name"]
        if self.params["erase_scope"] == "volume":
            info = self.info(self.params["device"])
            self.publish_info(info)
            name = name or info.get("VolumeName") or "Untitled"
            unchanged = (
                first(info, "FileSystemPersonality", "FilesystemName") == self.params["filesystem"]
                and info.get("VolumeName") == name
            )
        else:
            name = name or "Untitled"
            unchanged = self.disk_already_erased(name)
        if unchanged:
            return
        self.result["changed"] = True
        if self.module.check_mode:
            return
        args = ["eraseDisk" if self.params["erase_scope"] == "disk" else "eraseVolume"]
        args.extend([self.params["filesystem"], name, device_id(self.params["device"])])
        if self.params["erase_scope"] == "disk" and self.params["partition_scheme"]:
            args.append(self.params["partition_scheme"])
        self.run(args)

    # -- entry point ---------------------------------------------------------------

    def do_state(self):
        """Runs the state change the user asked for."""
        state = self.params["state"]
        if state not in ("present", "absent"):
            self.require("device")

        if self.module._diff and self.params["device"]:
            self.result["before"] = self.info(self.params["device"], allow_failure=True)

        if state == "present":
            self.state_present()
        elif state == "absent":
            self.state_absent()
        elif state == "mounted":
            self.state_mounted()
        elif state == "unmounted":
            self.state_unmounted()
        elif state == "ejected":
            self.state_ejected()
        elif state in OWNERSHIP_STATES:
            self.state_ownership()
        elif state == "erased":
            self.state_erased()

        if self.module._diff and self.params["device"]:
            self.result["after"] = self.info(self.params["device"], allow_failure=True)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(
                type="str",
                choices=["present", "absent", "mounted", "unmounted", "ejected", "owned", "unowned", "erased"],
            ),
            info_type=dict(type="str", choices=["disks", "device", "apfs", "volume_groups", "filesystems"]),
            device=dict(type="str"),
            container=dict(type="str"),
            volume_name=dict(type="str"),
            mount_point=dict(type="path"),
            force=dict(type="bool", default=False),
            filesystem=dict(type="str", default="APFS"),
            quota=dict(type="str"),
            reserve=dict(type="str"),
            mount_new_volume=dict(type="bool", default=True),
            erase_scope=dict(type="str", choices=["volume", "disk"], default="volume"),
            partition_scheme=dict(type="str", choices=["APM", "MBR", "GPT"]),
            erase_confirm=dict(type="bool", default=False),
        ),
        required_one_of=[["state", "info_type"]],
        mutually_exclusive=[["state", "info_type"]],
        supports_check_mode=True,
    )
    module.run_command_environ_update = dict(LANGUAGE="C", LC_ALL="C")

    diskutil = DiskUtil(module)
    if module.params["info_type"]:
        diskutil.do_info()
    else:
        diskutil.do_state()
    module.exit_json(**diskutil.result)


if __name__ == "__main__":
    main()
