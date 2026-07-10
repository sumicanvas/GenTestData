/*
 ** migrate/mast_jmcode.js
 ** 2024-06-10
 ** merge & migrate mast & jmcode to news_mig
 **
 ** NOTE: this script is idempotent with checkpointing,
 **       so you can run it multiple times without issues.
 */
import "dotenv/config";
import { pipeline } from "./pipeline.js";
import { migrate_conts } from "./cont.js";

let bAborted = false;
export function abortMigration() {
  bAborted = true;
}

export function createProgressBar(cp, cursor_y, startTime) {
  const VHEIHGT = parseInt(process.env.nWORKERS, 10) + 1;
  const canMoveCursor = Boolean(
    process.stdout.isTTY &&
      process.stdout.moveCursor &&
      process.stdout.cursorTo &&
      process.stdout.clearLine,
  );

  if (!canMoveCursor) {
    return (isFailed = false) => {
      if (isFailed) {
        console.log(`${cp._id}: Failed to update checkpoint !!`);
      }
    };
  }

  return (isFailed = false) => {
    if (bAborted) return;

    const elapsedMs = Date.now() - startTime;
    const elapsedSec = Math.floor(elapsedMs / 1000);

    const hours = Math.floor(elapsedSec / 3600);
    const minutes = Math.floor((elapsedSec % 3600) / 60);
    const seconds = elapsedSec % 60;

    const formattedHours = hours.toString().padStart(2, "0");
    const formattedMinutes = minutes.toString().padStart(2, "0");
    const formattedSeconds = seconds.toString().padStart(2, "0");
    const elapsedTime = `${formattedHours}:${formattedMinutes}:${formattedSeconds}`;

    if (isFailed) {
      process.stdout.moveCursor(0, cursor_y);
      process.stdout.clearLine();
      process.stdout.cursorTo(0);
      process.stdout.write(`${cp._id}: Failed to update checkpoint !!`);
    } else {
      const filled = Math.floor((cp.nDocsProcessed / cp.nDocs2Process) * 20);
      const empty = 20 - filled;
      const bar = "█".repeat(filled) + "-".repeat(empty);
      const progress = ((cp.nDocsProcessed / cp.nDocs2Process) * 100).toFixed(
        2,
      );

      process.stdout.moveCursor(0, cursor_y);
      process.stdout.clearLine();
      process.stdout.cursorTo(0);
      process.stdout.write(
        `${cp._id} ${bar} ${cp.nDocsProcessed}/${cp.nDocs2Process} (${progress}%)`,
      );
    }

    process.stdout.moveCursor(0, VHEIHGT - cursor_y);
    process.stdout.clearLine();
    process.stdout.cursorTo(0);
    process.stdout.write(`Elapsed Time: ${elapsedTime}`);
    process.stdout.moveCursor(0, -VHEIHGT);
  };
}

async function get_lastid_per_batch(co_mast, cp) {
  let pipeline_lastid = [
    ...pipeline.docs_per_batch,
    ...pipeline.lastid_per_batch,
  ];

  const stage_match = {
    $match: {
      _id: {
        $gt: cp.lastId,
        $lte: cp.maxInclusive,
      },
    },
  };
  pipeline_lastid[0] = stage_match;
  const lastid = await co_mast
    .aggregate(pipeline_lastid, { allowDiskUse: true })
    .toArray();

  return [lastid, stage_match];
}

async function build_transform_tmp(cp, co_mast, stage_match) {
  let pipeline_tmp = [
    ...pipeline.docs_per_batch,
    ...pipeline.newscode2id,
    ...pipeline.transform_tmp,
  ];
  pipeline_tmp[0] = stage_match;
  return await co_mast
    .aggregate(pipeline_tmp, { allowDiskUse: true })
    .toArray();
}

async function migrate_news_jmcode(db, docs) {
  let pipeline_migrate = [{ $documents: docs }, ...pipeline.join_news_jmcode];
  await db.aggregate(pipeline_migrate, { allowDiskUse: true }).toArray();
}

export async function migrate_news(db, cp, pbar) {
  const co_mast = db.collection(process.env.CO_MAST);
  const co_checkpoint = db.collection(process.env.CO_CHECKPOINT);

  let nTotalProc = 0;
  do {
    const [batchLastId, stage_match] = await get_lastid_per_batch(co_mast, cp);
    if (batchLastId.length === 0) {
      console.log(`${cp._id}: Migration Completed: ${cp.nDocsProcessed}`);
      break;
    }

    const docs = await build_transform_tmp(cp, co_mast, stage_match);
    await migrate_news_jmcode(db, docs);
    await migrate_conts(db, docs);

    cp.lastId = batchLastId[0].lastId;
    cp.nDocsProcessed += batchLastId[0].nDocs;
    pbar();

    const upResult = await co_checkpoint.updateOne(
      { _id: cp._id },
      { $set: { lastId: cp.lastId, nDocsProcessed: cp.nDocsProcessed } },
    );

    if (upResult.acknowledged !== true) {
      pbar(true);
      break;
    }

    if (bAborted) break;
  } while (true);
}
