import "dotenv/config";
import { MongoClient } from "mongodb";
import { ObjectId } from "mongodb";
import {
  migrate_news,
  createProgressBar,
  abortMigration,
} from "./mast_jmcode.js";

const nWORKERS = parseInt(process.env.nWORKERS, 10) || 8;
const client = new MongoClient(process.env.MONGODB_URI, {
  maxPoolSize: nWORKERS * 3,
});

let migPromises = [];

function canMoveCursor() {
  return Boolean(
    process.stdout.isTTY &&
      process.stdout.moveCursor &&
      process.stdout.cursorTo &&
      process.stdout.clearLine,
  );
}

process.on("SIGINT", async () => {
  abortMigration();

  if (canMoveCursor()) {
    process.stdout.moveCursor(0, nWORKERS + 2);
    process.stdout.cursorTo(0);
  }
  console.log("\nMigration aborted by user. Terminating...");
  await Promise.all(migPromises);
  await client.close();
  process.exit(0);
});

async function createMigrationTarget(db, co_to) {
  const collections = await db.listCollections({ name: co_to }).toArray();
  if (collections.length === 0) {
    console.log(`Creating migration target collection: ${co_to}`);
    await db.createCollection(co_to, {
      clusteredIndex: { key: { _id: 1 }, unique: true },
    });
  } else {
    console.log(`Migration target collection already exists: ${co_to}`);
  }
}

async function main() {
  await client.connect();
  const db = client.db(process.env.NEWSDB);
  const co_mast = db.collection(process.env.CO_MAST);

  await createMigrationTarget(db, process.env.CO_TO);

  const co_checkpoint = db.collection(process.env.CO_CHECKPOINT);
  let cp = await co_checkpoint.find({ _id: /^migrator_/ }).toArray();
  if (cp.length !== nWORKERS) {
    console.log(
      `Checkpoint count (${cp.length}) does not match number of workers (${nWORKERS}). Resetting checkpoints...`,
    );
    await co_checkpoint.deleteMany({ _id: /^migrator_/ });

    const pipeline_divide_docs = [
      {
        $bucketAuto: {
          groupBy: "$_id",
          buckets: nWORKERS,
          output: {
            nDocs: { $sum: 1 },
          },
        },
      },
      {
        $set: {
          minExclusive: "$_id.min",
          maxInclusive: "$_id.max",
          _id: "$$REMOVE",
        },
      },
      {
        $sort: { minExclusive: 1 },
      },
    ];

    console.log(
      `Dividing ${await co_mast.countDocuments()} documents into ${nWORKERS} buckets...`,
    );
    let buckets = await co_mast.aggregate(pipeline_divide_docs).toArray();
    buckets[0].minExclusive = new ObjectId("000000000000000000000000");

    cp = buckets.map((bucket, index) => ({
      _id: "migrator_" + (index + 1),
      lastId: bucket.minExclusive,
      maxInclusive: bucket.maxInclusive,
      nDocsProcessed: 0,
      nDocs2Process: bucket.nDocs,
    }));
    await co_checkpoint.insertMany(cp);
  }

  console.log(`Starting migration with ${nWORKERS} workers...`);

  let pbars = [];
  const startTime = Date.now();
  migPromises = cp.map(async (checkpoint, index) => {
    console.log(
      `${checkpoint._id} start ` +
        `(${checkpoint.lastId}, ${checkpoint.maxInclusive}] ` +
        `nDocs=${checkpoint.nDocs2Process - checkpoint.nDocsProcessed}`,
    );
    const pbar = createProgressBar(checkpoint, index, startTime);
    pbars.push(pbar);
    return await migrate_news(db, checkpoint, pbar);
  });
  console.log();
  for (let w of migPromises) console.log();
  console.log();
  console.log();
  if (canMoveCursor()) {
    process.stdout.moveCursor(0, -(nWORKERS + 2));
  }

  for (let pbar of pbars) pbar();

  await Promise.all(migPromises);

  await client.close();
  process.exit(0);
}

await main();
