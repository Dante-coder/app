# Copyright (C) 2022 CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

import io
from logging import Logger
from pathlib import Path
from typing import Tuple

import pytest
from cvat_sdk import Client
from cvat_sdk.api_client import exceptions, models
from cvat_sdk.core.proxies.tasks import ResourceType, Task

from shared.utils.config import USER_PASS


class TestIssueUsecases:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        changedb,  # force fixture call order to allow DB setup
        tmp_path: Path,
        fxt_logger: Tuple[Logger, io.StringIO],
        fxt_client: Client,
        fxt_stdout: io.StringIO,
        admin_user: str,
    ):
        self.tmp_path = tmp_path
        _, self.logger_stream = fxt_logger
        self.client = fxt_client
        self.stdout = fxt_stdout
        self.user = admin_user
        self.client.login((self.user, USER_PASS))

        yield

    @pytest.fixture
    def fxt_new_task(self, fxt_image_file: Path):
        task = self.client.tasks.create_from_data(
            spec={
                "name": "test_task",
                "labels": [{"name": "car"}, {"name": "person"}],
            },
            resource_type=ResourceType.LOCAL,
            resources=[str(fxt_image_file)],
            data_params={"image_quality": 80},
        )

        return task

    def test_can_retrieve_issue(self, fxt_new_task: Task):
        issue = self.client.issues.create(
            models.IssueWriteRequest(
                frame=0,
                position=[2.0, 4.0],
                job=fxt_new_task.get_jobs()[0].id,
                message="hello",
            )
        )

        retrieved_issue = self.client.issues.retrieve(issue.id)

        assert issue.id == retrieved_issue.id
        assert self.stdout.getvalue() == ""

    def test_can_list_issues(self, fxt_new_task: Task):
        issue = self.client.issues.create(
            models.IssueWriteRequest(
                frame=0,
                position=[2.0, 4.0],
                job=fxt_new_task.get_jobs()[0].id,
                message="hello",
                assignee=self.client.users.list()[0].id,
            )
        )

        issues = self.client.issues.list()

        assert any(issue.id == j.id for j in issues)
        assert self.stdout.getvalue() == ""

    def test_can_list_comments(self, fxt_new_task: Task):
        issue = self.client.issues.create(
            models.IssueWriteRequest(
                frame=0,
                position=[2.0, 4.0],
                job=fxt_new_task.get_jobs()[0].id,
                message="hello",
            )
        )
        comment = self.client.comments.create(models.CommentWriteRequest(issue.id, message="hi!"))
        issue.fetch()

        comment_ids = {c.id for c in issue.comments}

        assert len(comment_ids) == 2
        assert comment.id in comment_ids
        assert self.stdout.getvalue() == ""

    def test_can_modify_issue(self, fxt_new_task: Task):
        issue = self.client.issues.create(
            models.IssueWriteRequest(
                frame=0,
                position=[2.0, 4.0],
                job=fxt_new_task.get_jobs()[0].id,
                message="hello",
            )
        )

        issue.update(models.PatchedIssueWriteRequest(resolved=True))

        retrieved_issue = self.client.issues.retrieve(issue.id)
        assert retrieved_issue.resolved is True
        assert issue.resolved == retrieved_issue.resolved
        assert self.stdout.getvalue() == ""

    def test_can_remove_issue(self, fxt_new_task: Task):
        issue = self.client.issues.create(
            models.IssueWriteRequest(
                frame=0,
                position=[2.0, 4.0],
                job=fxt_new_task.get_jobs()[0].id,
                message="hello",
            )
        )

        issue.remove()

        with pytest.raises(exceptions.NotFoundException):
            issue.fetch()
        with pytest.raises(exceptions.NotFoundException):
            self.client.comments.retrieve(issue.comments[0].id)
        assert self.stdout.getvalue() == ""


class TestCommentUsecases:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        changedb,  # force fixture call order to allow DB setup
        tmp_path: Path,
        fxt_logger: Tuple[Logger, io.StringIO],
        fxt_client: Client,
        fxt_stdout: io.StringIO,
        admin_user: str,
    ):
        self.tmp_path = tmp_path
        _, self.logger_stream = fxt_logger
        self.client = fxt_client
        self.stdout = fxt_stdout
        self.user = admin_user
        self.client.login((self.user, USER_PASS))

        yield

    @pytest.fixture
    def fxt_new_task(self, fxt_image_file: Path):
        task = self.client.tasks.create_from_data(
            spec={
                "name": "test_task",
                "labels": [{"name": "car"}, {"name": "person"}],
            },
            resource_type=ResourceType.LOCAL,
            resources=[str(fxt_image_file)],
            data_params={"image_quality": 80},
        )

        return task

    def test_can_retrieve_comment(self, fxt_new_task: Task):
        issue = self.client.issues.create(
            models.IssueWriteRequest(
                frame=0,
                position=[2.0, 4.0],
                job=fxt_new_task.get_jobs()[0].id,
                message="hello",
            )
        )
        comment = self.client.comments.create(models.CommentWriteRequest(issue.id, message="hi!"))

        retrieved_comment = self.client.comments.retrieve(comment.id)

        assert comment.id == retrieved_comment.id
        assert self.stdout.getvalue() == ""

    def test_can_list_comments(self, fxt_new_task: Task):
        issue = self.client.issues.create(
            models.IssueWriteRequest(
                frame=0,
                position=[2.0, 4.0],
                job=fxt_new_task.get_jobs()[0].id,
                message="hello",
            )
        )
        comment = self.client.comments.create(models.CommentWriteRequest(issue.id, message="hi!"))

        comments = self.client.comments.list()

        assert any(comment.id == c.id for c in comments)
        assert self.stdout.getvalue() == ""

    def test_can_modify_comment(self, fxt_new_task: Task):
        issue = self.client.issues.create(
            models.IssueWriteRequest(
                frame=0,
                position=[2.0, 4.0],
                job=fxt_new_task.get_jobs()[0].id,
                message="hello",
            )
        )
        comment = self.client.comments.create(models.CommentWriteRequest(issue.id, message="hi!"))

        comment.update(models.PatchedCommentWriteRequest(message="bar"))

        retrieved_comment = self.client.comments.retrieve(comment.id)
        assert retrieved_comment.message == "bar"
        assert comment.message == retrieved_comment.message
        assert self.stdout.getvalue() == ""

    def test_can_remove_comment(self, fxt_new_task: Task):
        issue = self.client.issues.create(
            models.IssueWriteRequest(
                frame=0,
                position=[2.0, 4.0],
                job=fxt_new_task.get_jobs()[0].id,
                message="hello",
            )
        )
        comment = self.client.comments.create(models.CommentWriteRequest(issue.id, message="hi!"))

        comment.remove()

        with pytest.raises(exceptions.NotFoundException):
            comment.fetch()
        assert self.stdout.getvalue() == ""
