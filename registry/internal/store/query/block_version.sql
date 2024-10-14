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

-- name: GetBlocksWithLatestVersion :many
SELECT distinct on (b.id)
    b.id,
    b.name,
    bv.version,
    bv.specification,
    bv.documenatation_url,
    bv.docker_image,
    bv.created_at,
    bv.updated_at
FROM public.block_versions bv 
    INNER JOIN public.blocks b
    ON bv.block_id = b.id
ORDER BY b.id, bv.version desc;

-- name: GetBlockAllVersionByName :many
SELECT
    b.id,
    b.name,
    bv.version,
    bv.specification,
    bv.documenatation_url,
    bv.docker_image,
    bv.created_at,
    bv.updated_at
FROM public.block_versions bv
    INNER JOIN public.blocks b
    ON bv.block_id = b.id
WHERE name = $1
ORDER BY b.id, bv.version desc;
