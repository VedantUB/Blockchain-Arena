// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

contract Tracker {

    // Step 1: Struct to store item details
    struct Item {
        uint256 id;
        string name;
        address owner;
    }

    // Step 2: State variables
    mapping(uint256 => Item) public items; // itemId -> Item
    uint256 public itemCount; // auto-incremented ID

    // Step 3: Events
    event ItemRegistered(uint256 indexed id, address indexed owner, string name);
    event OwnershipTransferred(uint256 indexed id, address indexed from, address indexed to);

    // Step 4: Register a new item
    function registerItem(string memory name) public {
        itemCount++;
        items[itemCount] = Item(itemCount, name, msg.sender);
        emit ItemRegistered(itemCount, msg.sender, name);
    }

    // Step 5: Transfer ownership
    function transferOwnership(uint256 id, address newOwner) public {
        require(items[id].owner == msg.sender, "Not the owner");
        address previousOwner = items[id].owner;
        items[id].owner = newOwner;
        emit OwnershipTransferred(id, previousOwner, newOwner);
    }
}