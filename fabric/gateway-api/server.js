"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs/promises");
const { TextDecoder } = require("node:util");

const express = require("express");
const grpc = require("@grpc/grpc-js");
const { connect, hash, signers } = require("@hyperledger/fabric-gateway");

const utf8Decoder = new TextDecoder();

const app = express();
app.use(express.json({ limit: "1mb" }));

const PORT = Number(process.env.PORT || 8080);
const CHANNEL_NAME = process.env.FABRIC_CHANNEL_NAME || "mychannel";
const CHAINCODE_NAME = process.env.FABRIC_CHAINCODE_NAME || "prediction-ledger";
const MSP_ID = process.env.FABRIC_MSP_ID || "Org1MSP";
const GATEWAY_ENDPOINT = process.env.FABRIC_GATEWAY_ENDPOINT || "localhost:7051";
const CERT_PATH = process.env.FABRIC_CERT_PATH;
const PRIVATE_KEY_PATH = process.env.FABRIC_PRIVATE_KEY_PATH;
const TLS_ROOT_CERT_PATH = process.env.FABRIC_TLS_ROOT_CERT_PATH;
const TLS_HOSTNAME_OVERRIDE = process.env.FABRIC_TLS_HOSTNAME_OVERRIDE;

let gatewayPromise;

function csvEscape(value) {
  const text = String(value ?? "");
  if (/[",\n\r]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

function toCsv(chain) {
  const headers = [
    "index",
    "timestamp",
    "source",
    "image_name",
    "image_sha256",
    "model_dir",
    "top_k",
    "predictions",
    "previous_hash",
    "hash",
    "signature",
  ];
  const lines = [headers.join(",")];
  for (const block of chain) {
    lines.push(
      [
        block.index,
        block.timestamp,
        block.source,
        block.image_name,
        block.image_sha256,
        block.model_dir,
        block.top_k,
        JSON.stringify(block.predictions || []),
        block.previous_hash,
        block.hash,
        block.signature,
      ].map(csvEscape).join(","),
    );
  }
  return lines.join("\n");
}

async function loadContract() {
  if (gatewayPromise) {
    return gatewayPromise;
  }

  gatewayPromise = (async () => {
    if (!CERT_PATH || !PRIVATE_KEY_PATH || !TLS_ROOT_CERT_PATH) {
      throw new Error(
        "Missing Fabric identity config. Set FABRIC_CERT_PATH, FABRIC_PRIVATE_KEY_PATH, and FABRIC_TLS_ROOT_CERT_PATH.",
      );
    }

    const [credentials, privateKeyPem, tlsRootCert] = await Promise.all([
      fs.readFile(CERT_PATH),
      fs.readFile(PRIVATE_KEY_PATH),
      fs.readFile(TLS_ROOT_CERT_PATH),
    ]);
    const privateKey = crypto.createPrivateKey(privateKeyPem);
    const signer = signers.newPrivateKeySigner(privateKey);
    const sslCredentials = grpc.credentials.createSsl(tlsRootCert);
    const channelOptions = {};
    if (TLS_HOSTNAME_OVERRIDE) {
      channelOptions["grpc.ssl_target_name_override"] = TLS_HOSTNAME_OVERRIDE;
      channelOptions["grpc.default_authority"] = TLS_HOSTNAME_OVERRIDE;
    }

    const client = new grpc.Client(GATEWAY_ENDPOINT, sslCredentials, channelOptions);
    const gateway = connect({
      identity: { mspId: MSP_ID, credentials },
      signer,
      hash: hash.sha256,
      client,
    });
    const network = gateway.getNetwork(CHANNEL_NAME);
    const contract = network.getContract(CHAINCODE_NAME);

    return { client, gateway, contract };
  })();

  return gatewayPromise;
}

async function getContract() {
  const session = await loadContract();
  return session.contract;
}

function parseLimit(value) {
  if (value == null || value === "") {
    return undefined;
  }
  const limit = Number.parseInt(String(value), 10);
  return Number.isFinite(limit) && limit >= 0 ? limit : undefined;
}

async function evaluateChain(limit) {
  const contract = await getContract();
  const result = await contract.evaluateTransaction("ListPredictions");
  const chain = JSON.parse(utf8Decoder.decode(result));
  if (typeof limit === "number") {
    return chain.slice(Math.max(chain.length - limit, 0));
  }
  return chain;
}

async function evaluateValidation() {
  const contract = await getContract();
  const result = await contract.evaluateTransaction("ValidatePredictions");
  return JSON.parse(utf8Decoder.decode(result));
}

async function createPrediction(payload) {
  const contract = await getContract();
  const result = await contract.submitTransaction("CreatePrediction", JSON.stringify(payload));
  return JSON.parse(utf8Decoder.decode(result));
}

app.get("/health", async (_req, res) => {
  try {
    await getContract();
    res.json({ status: "ok", channel: CHANNEL_NAME, chaincode: CHAINCODE_NAME });
  } catch (error) {
    res.status(500).json({ status: "error", error: String(error.message || error) });
  }
});

app.post("/predictions", async (req, res) => {
  try {
    const payload = req.body || {};
    const required = ["source", "image_name", "image_sha256", "model_dir", "top_k", "predictions"];
    for (const field of required) {
      if (payload[field] === undefined || payload[field] === null) {
        res.status(400).json({ error: `Missing field: ${field}` });
        return;
      }
    }
    const block = await createPrediction(payload);
    res.status(201).json(block);
  } catch (error) {
    res.status(500).json({ error: String(error.message || error) });
  }
});

app.get("/predictions", async (req, res) => {
  try {
    const chain = await evaluateChain(parseLimit(req.query.limit));
    res.json(chain);
  } catch (error) {
    res.status(500).json({ error: String(error.message || error) });
  }
});

app.get("/predictions/validate", async (_req, res) => {
  try {
    const validation = await evaluateValidation();
    res.json(validation);
  } catch (error) {
    res.status(500).json({ error: String(error.message || error) });
  }
});

app.get("/predictions/export/json", async (req, res) => {
  try {
    const chain = await evaluateChain(parseLimit(req.query.limit));
    res.type("application/json").send(JSON.stringify(chain, null, 2));
  } catch (error) {
    res.status(500).json({ error: String(error.message || error) });
  }
});

app.get("/predictions/export/csv", async (req, res) => {
  try {
    const chain = await evaluateChain(parseLimit(req.query.limit));
    res.type("text/csv").send(toCsv(chain));
  } catch (error) {
    res.status(500).json({ error: String(error.message || error) });
  }
});

app.use((_req, res) => {
  res.status(404).json({ error: "Not found" });
});

app.listen(PORT, () => {
  console.log(`Fabric ledger API listening on http://127.0.0.1:${PORT}`);
  console.log(`Channel: ${CHANNEL_NAME}, chaincode: ${CHAINCODE_NAME}`);
});
