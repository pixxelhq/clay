-- name: CreateBlockVersion :one
INSERT INTO 
    public.block_versions (
        block_id,
        version,
        specification,
        documenatation_url,
        docker_image
    )
VALUES
    (
        $1,
        $2,
        $3,
        $4,
        $5
    ) RETURNING *;