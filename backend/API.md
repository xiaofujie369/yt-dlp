# Koyun yt-dlp API

All protected endpoints require:

```http
Authorization: Bearer <token>
```

Errors are returned as:

```json
{
  "error": {
    "code": "404",
    "message": "Task not found"
  }
}
```

## Auth

- `GET /api/auth/login` redirects to Koyun OAuth.
- `GET /api/auth/callback?code=...` exchanges the code and redirects to the frontend with `?token=...`.
- `POST /api/auth/logout` acknowledges logout.
- `GET /api/auth/me` returns the current user.

## User Tasks

- `POST /api/tasks`
- `GET /api/tasks?page=1&page_size=20`
- `GET /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/cancel`
- `POST /api/tasks/{task_id}/retry`
- `DELETE /api/tasks/{task_id}`
- `GET /api/files/{file_id}/download`

Create task body:

```json
{
  "url": "https://www.youtube.com/watch?v=xxxx",
  "task_type": "video",
  "quality": "bv*+ba/b"
}
```

## Admin

All admin endpoints require the `admin` role.

- `GET /api/admin/dashboard`
- `GET /api/admin/tasks`
- `GET /api/admin/tasks/{task_id}`
- `POST /api/admin/tasks/{task_id}/cancel`
- `POST /api/admin/tasks/{task_id}/retry`
- `DELETE /api/admin/tasks/{task_id}`
- `GET /api/admin/users?role=&status=&email=&username=&q=&page=1&page_size=20`
- `GET /api/admin/users/{user_id}`
- `PATCH /api/admin/users/{user_id}`
- `POST /api/admin/users/{user_id}/apply-role-template`
- `POST /api/admin/users/{user_id}/reset-quota`
- `POST /api/admin/users/{user_id}/add-quota`
- `POST /api/admin/users/{user_id}/disable`
- `POST /api/admin/users/{user_id}/enable`
- `POST /api/admin/users/{user_id}/ban`
- `POST /api/admin/users/{user_id}/unban`
- `GET /api/admin/users/{user_id}/tasks`
- `GET /api/admin/users/{user_id}/files`
- `GET /api/admin/files`
- `DELETE /api/admin/files/{file_id}`
- `GET /api/admin/domain-rules`
- `POST /api/admin/domain-rules`
- `PATCH /api/admin/domain-rules/{id}`
- `DELETE /api/admin/domain-rules/{id}`
- `GET /api/admin/ip-blacklist`
- `POST /api/admin/ip-blacklist`
- `DELETE /api/admin/ip-blacklist/{id}`
- `GET /api/admin/settings`
- `PATCH /api/admin/settings`
- `GET /api/admin/stats/daily`
- `GET /api/admin/stats/weekly`
- `GET /api/admin/stats/monthly`
- `GET /api/admin/logs`
