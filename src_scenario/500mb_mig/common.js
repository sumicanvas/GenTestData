import { MongoClient } from "mongodb";
import { appendFile, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";

const DEFAULT_DB = "newsdb";
const DEFAULT_COLLECTION = "news_mig_500";
const DEFAULT_INDEX = "news5_search_index";
const DEFAULT_LIMIT = 100;
const DEFAULT_SHCODE_PATH = "shcode.shcode";
const LOG_DIR = join(dirname(fileURLToPath(import.meta.url)), "logs");

function nowIso() {
  return new Date().toISOString();
}

function elapsedMs(startNs) {
  return Number(process.hrtime.bigint() - startNs) / 1_000_000;
}

function safeLogName(value) {
  return value.replace(/[^a-zA-Z0-9가-힣_-]+/g, "_");
}

function formatMql(collectionName, pipeline) {
  const collectionRef = /^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(collectionName)
    ? `db.${collectionName}`
    : `db.getCollection(${JSON.stringify(collectionName)})`;

  return `${collectionRef}.aggregate(${JSON.stringify(pipeline, null, 2)});`;
}

async function appendLog(scenario, message) {
  await mkdir(LOG_DIR, { recursive: true });
  const logPath = join(LOG_DIR, `${safeLogName(scenario)}.log`);
  await appendFile(logPath, `${message}\n`, "utf-8");
}

async function printAndLog(scenario, message) {
  console.error(message);
  await appendLog(scenario, message);
}

export function parseArgs(argv = process.argv.slice(2)) {
  const args = {};

  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) {
      continue;
    }

    const withoutPrefix = token.slice(2);
    if (withoutPrefix.includes("=")) {
      const [key, ...rest] = withoutPrefix.split("=");
      args[key] = rest.join("=");
      continue;
    }

    const next = argv[i + 1];
    if (next && !next.startsWith("--")) {
      args[withoutPrefix] = next;
      i += 1;
    } else {
      args[withoutPrefix] = true;
    }
  }

  return args;
}

function toInt(value, fallback) {
  if (value === undefined || value === true || value === "") {
    return fallback;
  }
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed) || parsed <= 0) {
    throw new Error(`Invalid positive integer: ${value}`);
  }
  return parsed;
}

function getConfig(args) {
  return {
    uri: args.uri || process.env.MONGODB_URI,
    dbName: args.db || DEFAULT_DB,
    collectionName: args.collection || DEFAULT_COLLECTION,
    indexName: args.index || DEFAULT_INDEX,
    limit: toInt(args.limit, DEFAULT_LIMIT),
    dryRun: Boolean(args["dry-run"]),
    shcodePath: args["shcode-path"] || DEFAULT_SHCODE_PATH,
  };
}

async function promptMissingValues(args, inputs) {
  const missing = inputs.filter((item) => !args[item.key]);
  if (missing.length === 0) {
    return Object.fromEntries(inputs.map((item) => [item.key, args[item.key]]));
  }

  if (!input.isTTY) {
    const names = missing.map((item) => `--${item.key}`).join(", ");
    throw new Error(`Missing required arguments: ${names}`);
  }

  const rl = createInterface({ input, output });
  try {
    for (const item of missing) {
      const suffix = item.example ? ` (예: ${item.example})` : "";
      const answer = await rl.question(`${item.label}${suffix}: `);
      if (!answer.trim()) {
        throw new Error(`Missing value for ${item.key}`);
      }
      args[item.key] = answer.trim();
    }
  } finally {
    rl.close();
  }

  return Object.fromEntries(inputs.map((item) => [item.key, args[item.key]]));
}

function printHelp({ scenario, description, inputs }) {
  const inputArgs = inputs.map((item) => `--${item.key} <value>`).join(" ");
  const inputLines = inputs.length
    ? inputs.map((item) => `  --${item.key}: ${item.label}${item.example ? `, 예: ${item.example}` : ""}`).join("\n")
    : "  추가 입력값 없음";

  console.log(`
${scenario}
${description}

Usage:
  node ${process.argv[1]} ${inputArgs} [--limit 100] [--dry-run]

Required inputs:
${inputLines}

Common options:
  --uri <mongodb-uri>       기본값: MONGODB_URI 환경변수
  --db <database>           기본값: ${DEFAULT_DB}
  --collection <collection> 기본값: ${DEFAULT_COLLECTION}
  --index <search-index>    기본값: ${DEFAULT_INDEX}
  --shcode-path <path>      기본값: ${DEFAULT_SHCODE_PATH}
  --limit <number>          기본값: ${DEFAULT_LIMIT}
  --dry-run                 MongoDB 접속 없이 MQL만 출력
  --no-log                  로그 파일 기록 비활성화
`);
}

export function projectStage({ score = false, highlights = false } = {}) {
  const projection = {
    _id: 1,
    newscode_ts: 1,
    title: 1,
    contents: 1,
    dgubun: 1,
    shcode: 1,
  };

  if (score) {
    projection.score = { $meta: "searchScore" };
  }
  if (highlights) {
    projection.highlights = { $meta: "searchHighlights" };
  }

  return { $project: projection };
}

export function equalsFilter(path, value) {
  return {
    equals: {
      path,
      value,
    },
  };
}

export function textMust(query) {
  return {
    text: {
      query,
      path: ["title", "contents"],
      matchCriteria: "all",
    },
  };
}

export function noKeywordPipeline({ indexName, limit, filters }) {
  return [
    {
      $search: {
        index: indexName,
        compound: {
          filter: filters,
        },
        sort: {
          newscode_ts: -1,
        },
      },
    },
    { $limit: limit },
    projectStage(),
  ];
}

export function keywordPipeline({ indexName, limit, query, filters = [], highlight = false }) {
  const compound = {
    must: [textMust(query)],
  };

  if (filters.length > 0) {
    compound.filter = filters;
  }

  const search = {
    index: indexName,
    compound,
    sort: {
      score: { $meta: "searchScore" },
      newscode_ts: -1,
    },
  };

  if (highlight) {
    search.highlight = {
      path: ["title", "contents"],
    };
  }

  return [
    { $search: search },
    { $limit: limit },
    projectStage({ score: true, highlights: highlight }),
  ];
}

function scoreProjectStage() {
  return {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      score: 1,
    },
  };
}

export function fuzzyPipeline({ indexName, limit, query, titleBoost = 5, contentsBoost = 1, minScore = 1 }) {
  const fuzzy = {
    maxEdits: 1,
    prefixLength: 1,
    maxExpansions: 50,
  };

  const pipeline = [
    {
      $search: {
        index: indexName,
        compound: {
          should: [
            {
              text: {
                query,
                path: "title",
                matchCriteria: "all",
                fuzzy,
                score: { boost: { value: titleBoost } },
              },
            },
            {
              text: {
                query,
                path: "contents",
                matchCriteria: "all",
                fuzzy,
                score: { boost: { value: contentsBoost } },
              },
            },
          ],
          minimumShouldMatch: 1,
        },
        sort: {
          score: { $meta: "searchScore" },
          newscode_ts: -1,
        },
      },
    },
    {
      $addFields: {
        score: { $meta: "searchScore" },
      },
    },
  ];

  if (minScore > 0) {
    pipeline.push({
      $match: {
        score: { $gte: minScore },
      },
    });
  }

  pipeline.push({ $limit: limit }, scoreProjectStage());
  return pipeline;
}

export async function runScenario({ scenario, description, inputs = [], buildPipeline }) {
  const args = parseArgs();
  if (args.help) {
    printHelp({ scenario, description, inputs });
    return;
  }

  const config = getConfig(args);
  const values = await promptMissingValues(args, inputs);
  const pipeline = buildPipeline({ ...config, ...values, args });
  const loggingEnabled = !args["no-log"];

  if (config.dryRun) {
    const dryRunMessage = `[${nowIso()}] ${scenario} dry-run: MongoDB에 접속하지 않고 MQL만 출력합니다.`;
    if (loggingEnabled) {
      await printAndLog(scenario, dryRunMessage);
    } else {
      console.error(dryRunMessage);
    }
    console.log(formatMql(config.collectionName, pipeline));
    return;
  }

  if (!config.uri) {
    throw new Error("MONGODB_URI 환경변수를 설정하거나 --uri 옵션을 전달하세요.");
  }

  const client = new MongoClient(config.uri);

  try {
    await client.connect();

    const mqlMessage = `실행 MQL:\n${formatMql(config.collectionName, pipeline)}`;
    if (loggingEnabled) {
      await printAndLog(scenario, mqlMessage);
    } else {
      console.error(mqlMessage);
    }

    const startAt = nowIso();
    const startNs = process.hrtime.bigint();
    const startMessage = `쿼리시작전: ${startAt} db=${config.dbName} collection=${config.collectionName} limit=${config.limit}`;

    if (loggingEnabled) {
      await printAndLog(scenario, startMessage);
    } else {
      console.error(startMessage);
    }

    const documents = await client
      .db(config.dbName)
      .collection(config.collectionName)
      .aggregate(pipeline)
      .toArray();

    const endAt = nowIso();
    const durationMs = elapsedMs(startNs);
    const endMessage = `쿼리수행후: ${endAt} rows=${documents.length}`;
    const durationMessage = `전체수행시간: ${(durationMs / 1000).toFixed(2)} 초`;

    if (loggingEnabled) {
      await printAndLog(scenario, endMessage);
    } else {
      console.error(endMessage);
    }

    console.log(JSON.stringify(documents, null, 2));

    if (loggingEnabled) {
      await printAndLog(scenario, durationMessage);
    } else {
      console.error(durationMessage);
    }
  } catch (error) {
    const failAt = nowIso();
    const failMessage = `쿼리실패: ${failAt} error=${error.message}`;

    if (loggingEnabled) {
      await printAndLog(scenario, failMessage);
    } else {
      console.error(failMessage);
    }

    throw error;
  } finally {
    await client.close();
  }
}
