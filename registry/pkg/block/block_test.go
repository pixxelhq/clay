package block

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"testing"

	mock_store "registry/internal/store/mock"
	store "registry/internal/store/sqlc"

	"github.com/golang/mock/gomock"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

var reqBlock = &Block{
	Name:             "Test Block",
	Kind:             "example",
	Type:             "exampleType",
	Version:          "1.0.0",
	DocumentationURL: "http://example.com",
	DockerImage:      "example/image:latest",
	Specification: &Specification{
		Version:     "1.0.0",
		Title:       "Test Specification",
		Description: "This is a test specification",
		Author:      "Author Name",
		Tags:        []string{"tag1", "tag2"},
		Parameters:  json.RawMessage(`{}`),
		Inputs:      json.RawMessage(`{}`),
		Outputs:     json.RawMessage(`{}`),
		Build:       json.RawMessage(`{}`),
	},
}

func TestCreate(t *testing.T) {
	ctrl := gomock.NewController(t)
	defer ctrl.Finish()

	mockStore := mock_store.NewMockStore(ctrl)
	service := New(mockStore)

	tests := []struct {
		name          string
		input         *Block
		mockSetup     func()
		expectedError error
	}{
		{
			name:  "successful creation",
			input: reqBlock,
			mockSetup: func() {
				mockStore.EXPECT().ExecWithTx(gomock.Any(), gomock.Any()).
					DoAndReturn(func(ctx context.Context, fn func(q store.Querier) (interface{}, error)) (interface{}, error) {
						q := mockStore

						upsertedBlock := store.Block{
							ID:   uuid.New(),
							Name: "Test Block",
							Kind: "example",
							Type: "exampleType",
						}

						q.EXPECT().UpsertBlock(gomock.Any(), store.UpsertBlockParams{
							Name: "Test Block",
							Kind: "example",
							Type: "exampleType",
						}).Return(upsertedBlock, nil)

						specByte, _ := json.Marshal(&Specification{
							Version:     "1.0.0",
							Title:       "Test Specification",
							Description: "This is a test specification",
							Author:      "Author Name",
							Tags:        []string{"tag1", "tag2"},
							Parameters:  json.RawMessage(`{}`),
							Inputs:      json.RawMessage(`{}`),
							Outputs:     json.RawMessage(`{}`),
							Build:       json.RawMessage(`{}`),
						})

						bv := store.BlockVersion{
							ID:                uuid.New(),
							Version:           "1.0.0",
							BlockID:           upsertedBlock.ID,
							Specification:     specByte,
							DocumenatationUrl: sql.NullString{String: "http://example.com", Valid: true},
							DockerImage:       sql.NullString{String: "example/image:latest", Valid: true},
						}

						q.EXPECT().CreateBlockVersion(gomock.Any(), store.CreateBlockVersionParams{
							BlockID:           upsertedBlock.ID,
							Version:           "1.0.0",
							Specification:     specByte,
							DocumenatationUrl: sql.NullString{String: "http://example.com", Valid: true},
							DockerImage:       sql.NullString{String: "example/image:latest", Valid: true},
						}).Return(bv, nil)

						return fn(q)
					})
			},
			expectedError: nil,
		},
		{
			name: "error on upsert block",
			input: &Block{
				Name: "Test Block",
				Kind: "example",
				Type: "exampleType",
			},
			mockSetup: func() {
				mockStore.EXPECT().ExecWithTx(gomock.Any(), gomock.Any()).
					DoAndReturn(func(ctx context.Context, fn func(q store.Querier) (interface{}, error)) (interface{}, error) {
						q := mockStore

						q.EXPECT().UpsertBlock(gomock.Any(), store.UpsertBlockParams{
							Name: "Test Block",
							Kind: "example",
							Type: "exampleType",
						}).Return(store.Block{}, errors.New("upsert error"))

						return fn(q)
					})
			},
			expectedError: errors.New("upsert error"),
		},
		{
			name: "error on create block version",
			input: &Block{
				Name:             "Test Block",
				Kind:             "example",
				Type:             "exampleType",
				Specification:    &Specification{},
				Version:          "1.0.0",
				DocumentationURL: "http://example.com",
				DockerImage:      "example/image:latest",
			},
			mockSetup: func() {
				mockStore.EXPECT().ExecWithTx(gomock.Any(), gomock.Any()).
					DoAndReturn(func(ctx context.Context, fn func(q store.Querier) (interface{}, error)) (interface{}, error) {
						q := mockStore

						upsertedBlock := store.Block{
							ID:   uuid.New(),
							Name: "Test Block",
							Kind: "example",
							Type: "exampleType",
						}

						q.EXPECT().UpsertBlock(gomock.Any(), store.UpsertBlockParams{
							Name: "Test Block",
							Kind: "example",
							Type: "exampleType",
						}).Return(upsertedBlock, nil)

						specByte, _ := json.Marshal(&Specification{})

						q.EXPECT().CreateBlockVersion(gomock.Any(), store.CreateBlockVersionParams{
							BlockID:           upsertedBlock.ID,
							Version:           "1.0.0",
							Specification:     specByte,
							DocumenatationUrl: sql.NullString{String: "http://example.com", Valid: true},
							DockerImage:       sql.NullString{String: "example/image:latest", Valid: true},
						}).Return(store.BlockVersion{}, errors.New("create block version error"))

						return fn(q)
					})
			},
			expectedError: errors.New("create block version error"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.mockSetup()
			resp, err := service.Create(context.Background(), tt.input)
			if tt.expectedError != nil {
				assert.Error(t, err)
				assert.Equal(t, tt.expectedError.Error(), err.Error())
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, resp)
			}
		})
	}
}
