"use strict";

const { Contract } = require("fabric-contract-api");
const crypto = require("crypto");

function stableValue(value) {
  if (Array.isArray(value)) {
    return value.map((item) => stableValue(item));
  }
  if (value && typeof value === "object") {
    return Object.keys(value)
      .sort()
      .reduce((acc, key) => {
        acc[key] = stableValue(value[key]);
        return acc;
      }, {});
  }
  return value;
}

function canonicalJson(value) {
  return JSON.stringify(stableValue(value));
}

function sha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

class PredictionLedgerContract extends Contract {
  async _loadChain(ctx) {
    const iterator = await ctx.stub.getStateByRange("", "");
    const chain = [];
    while (true) {
      const item = await iterator.next();
      if (item.value) {
        try {
          chain.push(JSON.parse(item.value.toString("utf8")));
        } catch (err) {
          // Skip malformed records so validation can still report a failure.
        }
      }
      if (item.done) {
        await iterator.close();
        break;
      }
    }
    chain.sort((a, b) => Number(a.index) - Number(b.index));
    return chain;
  }

  async CreatePrediction(ctx, payloadJson) {
    const payload = typeof payloadJson === "string" ? JSON.parse(payloadJson) : payloadJson;
    const chain = await this._loadChain(ctx);
    const previousHash = chain.length ? chain[chain.length - 1].hash : "0".repeat(64);
    const block = {
      index: chain.length,
      timestamp: new Date().toISOString(),
      source: payload.source,
      image_name: payload.image_name,
      image_sha256: payload.image_sha256,
      model_dir: payload.model_dir,
      top_k: Number(payload.top_k),
      predictions: payload.predictions || [],
      previous_hash: previousHash
    };
    block.hash = sha256(canonicalJson(block));
    block.signature = ctx.stub.getTxID();
    await ctx.stub.putState(`prediction:${block.index}`, Buffer.from(JSON.stringify(block)));
    return JSON.stringify(block);
  }

  async GetPrediction(ctx, index) {
    const raw = await ctx.stub.getState(`prediction:${Number(index)}`);
    if (!raw || raw.length === 0) {
      return "";
    }
    return raw.toString("utf8");
  }

  async ListPredictions(ctx) {
    return JSON.stringify(await this._loadChain(ctx));
  }

  async ValidatePredictions(ctx) {
    const chain = await this._loadChain(ctx);
    for (let i = 0; i < chain.length; i += 1) {
      const block = chain[i];
      const expectedPrev = i === 0 ? "0".repeat(64) : chain[i - 1].hash;
      const payload = {
        index: block.index,
        timestamp: block.timestamp,
        source: block.source,
        image_name: block.image_name,
        image_sha256: block.image_sha256,
        model_dir: block.model_dir,
        top_k: block.top_k,
        predictions: block.predictions,
        previous_hash: block.previous_hash
      };
      const expectedHash = sha256(canonicalJson(payload));
      if (block.previous_hash !== expectedPrev) {
        return JSON.stringify({ valid: false, broken_index: i, length: chain.length, reason: "broken-link" });
      }
      if (block.hash !== expectedHash) {
        return JSON.stringify({ valid: false, broken_index: i, length: chain.length, reason: "hash-mismatch" });
      }
    }
    return JSON.stringify({ valid: true, length: chain.length });
  }
}

module.exports = PredictionLedgerContract;
