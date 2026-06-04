package main

import (
	"encoding/json"
	"fmt"
	"sort"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

type PredictionLedgerContract struct {
	contractapi.Contract
}

func (c *PredictionLedgerContract) RecordBlock(ctx contractapi.TransactionContextInterface, blockJSON string) error {
	var block map[string]any
	if err := json.Unmarshal([]byte(blockJSON), &block); err != nil {
		return fmt.Errorf("invalid block json: %w", err)
	}

	hash, _ := block["hash"].(string)
	if hash == "" {
		return fmt.Errorf("block hash is required")
	}

	key := "prediction:" + ctx.GetStub().GetTxID()
	existing, err := ctx.GetStub().GetState(key)
	if err != nil {
		return err
	}
	if existing != nil {
		return fmt.Errorf("block already exists for transaction %s", ctx.GetStub().GetTxID())
	}

	return ctx.GetStub().PutState(key, []byte(blockJSON))
}

func (c *PredictionLedgerContract) ListBlocks(ctx contractapi.TransactionContextInterface) (string, error) {
	iter, err := ctx.GetStub().GetStateByRange("prediction:", "prediction;")
	if err != nil {
		return "", err
	}
	defer iter.Close()

	var blocks []map[string]any
	for iter.HasNext() {
		response, err := iter.Next()
		if err != nil {
			return "", err
		}

		var block map[string]any
		if err := json.Unmarshal(response.Value, &block); err != nil {
			return "", err
		}
		blocks = append(blocks, block)
	}

	sort.Slice(blocks, func(i, j int) bool {
		left, lok := blocks[i]["index"].(float64)
		right, rok := blocks[j]["index"].(float64)
		if lok && rok && left != right {
			return left < right
		}

		leftTime, _ := blocks[i]["timestamp"].(string)
		rightTime, _ := blocks[j]["timestamp"].(string)
		if leftTime != rightTime {
			return leftTime < rightTime
		}

		leftHash, _ := blocks[i]["hash"].(string)
		rightHash, _ := blocks[j]["hash"].(string)
		return leftHash < rightHash
	})

	payload, err := json.Marshal(blocks)
	if err != nil {
		return "", err
	}
	return string(payload), nil
}

func (c *PredictionLedgerContract) GetBlockCount(ctx contractapi.TransactionContextInterface) (int, error) {
	iter, err := ctx.GetStub().GetStateByRange("prediction:", "prediction;")
	if err != nil {
		return 0, err
	}
	defer iter.Close()

	count := 0
	for iter.HasNext() {
		if _, err := iter.Next(); err != nil {
			return 0, err
		}
		count++
	}
	return count, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&PredictionLedgerContract{})
	if err != nil {
		panic(fmt.Sprintf("failed to create chaincode: %v", err))
	}

	if err := chaincode.Start(); err != nil {
		panic(fmt.Sprintf("failed to start chaincode: %v", err))
	}
}

