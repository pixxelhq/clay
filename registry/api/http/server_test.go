package http

import (
	"path/filepath"
	"testing"

	"github.com/pixxelhq/clay/registry/config"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

const (
	testDBUser     = "clayuser"
	testDBPassword = "s3cr3t-pw"
	testDBHost     = "127.0.0.1"
	testDBName     = "clay_test_db"
)

func newUnreachableDBServer(t *testing.T) *Server {
	t.Helper()
	migrationPath, err := filepath.Abs("../../internal/store/migrations")
	require.NoError(t, err)
	return &Server{
		Cfg: &config.Config{
			DBUserName:      testDBUser,
			DBPassword:      testDBPassword,
			DBHost:          testDBHost,
			DBPort:          1, // nothing listens here, so connecting fails fast
			DBName:          testDBName,
			DBMigrationPath: "file://" + migrationPath,
		},
	}
}

const wantConnErr = `cannot connect to database "clay_test_db" on host "127.0.0.1"`

func assertNoCredentials(t *testing.T, err error) {
	t.Helper()
	require.Error(t, err)
	msg := err.Error()
	assert.NotContains(t, msg, testDBPassword)
	assert.NotContains(t, msg, testDBUser)
	assert.NotContains(t, msg, "postgres://")
}

func TestRunMigrationConnectionErrorHasNoCredentials(t *testing.T) {
	err := newUnreachableDBServer(t).RunMigration()
	assertNoCredentials(t, err)
	assert.EqualError(t, err, wantConnErr)
}

func TestConfigureStoreConnectionErrorHasNoCredentials(t *testing.T) {
	err := newUnreachableDBServer(t).ConfigureStore()
	assertNoCredentials(t, err)
	assert.EqualError(t, err, wantConnErr)
}

func TestRunMigrationBadMigrationPathIsNotAConnectionError(t *testing.T) {
	svr := newUnreachableDBServer(t)
	svr.Cfg.DBMigrationPath = "file://" + filepath.Join(t.TempDir(), "missing")

	err := svr.RunMigration()
	assertNoCredentials(t, err)
	assert.Contains(t, err.Error(), "failed to load migrations from "+svr.Cfg.DBMigrationPath)
	assert.NotContains(t, err.Error(), "cannot connect to database")
}
