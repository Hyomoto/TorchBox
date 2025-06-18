# Library: login
---

**Requires Permissions:**[`login`]

Library for user login and management, including finding users, checking passwords, setting passwords,
and creating new users.  This Library requires the 'login' permission to be used.

## `check_password(user, password)`

> Check if the provided password matches the user's password.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| user | `User` |  |
| password | `str` |  |

#### **Returns:**

*- bool: True if the password matches, otherwise False.*



## `delete_user(user)`

> Delete the specified user.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| user | `User` |  |

#### **Returns:**

_None_



## `find_user(username)`

> Find a user by username.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| username | `str` |  |

#### **Returns:**

*- User: The user object if found, otherwise None.*



## `new_user(username, password)`

> Create a new user with the given username and password.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| username | `str` |  |
| password | `str` |  |

#### **Returns:**

*- User: The newly created user object.*



## `set_password(user, password)`

> Set the user's password.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| user | `User` |  |
| password | `str` |  |

#### **Returns:**

_None_




---
